"""Main entry point for the Multi-Client Web Scraper.

Supports running both as a module (python -m generic_scraper.app)
and directly as a script (python generic_scraper/app.py).
"""

import asyncio
import json
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from rich.progress import Progress
from rich.table import Table

# Import client modules to trigger auto-registration
# This registers demo, electronics_supplier, test_supplier, G2S, etc.
import clients  # noqa: F401
import G2S  # noqa: F401
from client_config import registry

# Direct imports - app.py is run as script by GUI subprocess
from config import get_config
from email_utils import send_email
from generic_scraper import process_part_number_generic
from io_utils import (
    generate_summary_report,
    read_part_numbers_in_chunks,
    save_results_atomic,
    validate_input_schema,
    validate_output_schema,
)
from log_utils import mask_secrets, setup_logging
from ui import console

app = typer.Typer()

class OutputFormat(str, Enum):
    csv = "csv"
    json = "json"
    excel = "excel"

@app.command()  # type: ignore[misc]
def main(
    input_csv: Path = typer.Option(..., "--input-csv", help="Input CSV file path"),
    output_csv: Path = typer.Option(..., "--output-csv", help="Output file path (CSV/JSON/Excel)"),
    client: str = typer.Option(..., "--client", help="Client ID (e.g., 'g2s')"),
    log_level: Optional[str] = typer.Option(None, help="Log level (INFO, DEBUG, etc.)"),
    dry_run: bool = typer.Option(False, help="Dry run mode (no writes)"),
    output_format: OutputFormat = typer.Option(OutputFormat.csv, help="Output format: csv, json, or excel"),
    resume: bool = typer.Option(False, help="Resume from existing output by skipping already processed part numbers"),
) -> None:
    """Run the Generic Scraper with required parameters (designed to be called by GUI)."""
    config = get_config()
    if log_level:
        config = config.__class__(**{**config.__dict__, 'log_level': log_level})

    # Client selection - parameter is now required by typer
    client_config = registry.get_client(client)
    if not client_config:
        available_clients = registry.get_client_ids()
        console.print(f"[red]Client '{client}' not found. Available clients: {', '.join(available_clients)}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Selected client: {client_config.client_name}[/green]")

    # Proxy connectivity test - run when proxy is configured
    from typing import Any

    import aiohttp
    
    async def proxy_test() -> None:
        if not config.proxy_username or not config.proxy_password:
            console.print("[yellow]Skipping proxy test - no proxy credentials configured[/yellow]")
            return

        console.print(f"[cyan]Testing proxy connection: {config.proxy_host}[/cyan]")
        test_url = "https://ipapi.co/json/"  # HTTPS to avoid plaintext
        import random as _random
        attempts = 3
        last_err: str | None = None
        for attempt in range(attempts):
            try:
                # Use proper SSL context handling
                ssl_context: Any = None if config.verify_ssl else False
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                timeout = aiohttp.ClientTimeout(total=10)
                proxy = f"http://{config.proxy_host}"  # no credentials in URL
                proxy_auth = aiohttp.BasicAuth(config.proxy_username, config.proxy_password)
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    async with session.get(test_url, proxy=proxy, proxy_auth=proxy_auth) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            console.print("[green]✅ Proxy test successful![/green]")

                            # Display comprehensive proxy information
                            console.print("[cyan]Proxy Connection Details:[/cyan]")
                            console.print(f"  🌐 External IP: [bold blue]{data.get('ip', 'unknown')}[/bold blue]")
                            console.print(f"  📍 Location: [yellow]{data.get('city', 'unknown')}, {data.get('region', 'unknown')}, {data.get('country_name', 'unknown')}[/yellow]")
                            console.print(f"  🏢 ISP: [magenta]{data.get('org', 'unknown')}[/magenta]")
                            console.print(f"  🌍 Country Code: [green]{data.get('country_code', 'unknown')}[/green]")
                            console.print(f"  ⏰ Timezone: [cyan]{data.get('timezone', 'unknown')}[/cyan]")

                            # Show additional fields if available
                            if data.get('postal'):
                                console.print(f"  📮 Postal Code: [dim]{data.get('postal')}[/dim]")
                            if data.get('latitude') and data.get('longitude'):
                                console.print(f"  🗺️  Coordinates: [dim]{data.get('latitude')}, {data.get('longitude')}[/dim]")

                            # Create a compact summary of key fields
                            key_fields = {
                                'ip': data.get('ip'),
                                'city': data.get('city'),
                                'region': data.get('region'),
                                'country': data.get('country_name'),
                                'isp': data.get('org'),
                                'timezone': data.get('timezone')
                            }
                            console.print(f"[dim]Summary: {' | '.join([f'{k}={v}' for k, v in key_fields.items() if v])}[/dim]")
                            return
                        last_err = f"HTTP status: {resp.status}"
                        raise RuntimeError(last_err)
            except Exception as e:
                safe = mask_secrets(str(e))
                last_err = safe if safe else e.__class__.__name__
                if attempt < attempts - 1:
                    # Exponential backoff with jitter: 1s, 2s, ...
                    delay = (2 ** attempt) + _random.uniform(0, 0.5)
                    console.print(f"[yellow]Proxy test attempt {attempt + 1} failed, retrying in {delay:.1f}s...[/yellow]")
                    await asyncio.sleep(delay)
                    continue
            console.print(f"[red]❌ Proxy test failed after {attempts} attempts: {last_err}[/red]")
            console.print("[yellow]⚠️  Scraping may fail without working proxy. Check your proxy credentials.[/yellow]")
    asyncio.run(proxy_test())

    setup_logging(config.log_file, config.log_level)
    console.print("[bold cyan] Multi-Client Web Scraper[/bold cyan]")

    # Input and output files are now required by typer - no validation needed

    # Ensure Path type
    if not isinstance(input_csv, Path):
        input_csv = Path(input_csv)
    if not isinstance(output_csv, Path):
        output_csv = Path(output_csv)

    # Input validation
    if not input_csv or not input_csv.is_file():
        safe_msg = mask_secrets(
            f"Input file '{input_csv}' does not exist or is not a file. Exiting."
        )
        console.print(f"[red]{safe_msg}[/red]")
        raise typer.Exit(1)
    if output_csv.exists() and not output_csv.is_file():
        safe_msg = mask_secrets(f"Output path '{output_csv}' exists and is not a file. Exiting.")
        console.print(f"[red]{safe_msg}[/red]")
        raise typer.Exit(1)

    # Schema validation
    try:
        validate_input_schema(input_csv)
        if output_csv.exists():
            validate_output_schema(output_csv, client_config.output_columns)
    except Exception as e:
        console.print(f"[red]{mask_secrets(str(e))}[/red]")
        raise typer.Exit(1) from e

    all_results: list[dict[str, str]] = []
    try:
        start_time = time.time()
        semaphore = asyncio.Semaphore(config.concurrency_limit)

        import re
        def is_valid_part_number(part_number: str) -> bool:
            return bool(re.match(r'^[\w\-/\.]{1,64}$', str(part_number).strip()))

        # Compute total items (best-effort; count non-empty lines)
        total_items: Optional[int] = None
        try:
            with open(input_csv, encoding="utf-8", errors="ignore") as f:
                total_items = sum(1 for line in f if line.strip())
        except Exception:
            total_items = None

        # Preload processed items if resume enabled and output exists
        processed: set[str] = set()
        if resume and output_csv.exists():
            try:
                pre_count = 0
                if output_format == OutputFormat.csv:
                    try:
                        df_prev = pd.read_csv(output_csv, usecols=["Part Number", "Status"])
                    except Exception:
                        df_prev = pd.read_csv(output_csv)
                    if "Part Number" in df_prev.columns:
                        # Only skip items that were successfully processed (not FetchError or Error)
                        if "Status" in df_prev.columns:
                            processed = set(
                                df_prev[~df_prev["Status"].isin(["FetchError", "Error"])]["Part Number"]
                                .dropna()
                                .astype(str)
                                .tolist()
                            )
                        else:
                            processed = set(df_prev["Part Number"].dropna().astype(str).tolist())
                elif output_format == OutputFormat.json:
                    with open(output_csv, encoding="utf-8") as f:
                        data_prev = json.load(f)
                    # Only skip items that were successfully processed (not FetchError or Error)
                    processed = {
                        str(item.get("Part Number"))
                        for item in data_prev
                        if isinstance(item, dict)
                        and item.get("Part Number")
                        and item.get("Status") not in ["FetchError", "Error"]
                    }
                elif output_format == OutputFormat.excel:
                    try:
                        # requires openpyxl
                        df_prev = pd.read_excel(output_csv, usecols=["Part Number", "Status"])
                    except Exception:  # noqa: BLE001
                        df_prev = pd.read_excel(output_csv)
                    if "Part Number" in df_prev.columns:
                        # Only skip items that were successfully processed (not FetchError or Error)
                        if "Status" in df_prev.columns:
                            processed = set(
                                df_prev[~df_prev["Status"].isin(["FetchError", "Error"])]["Part Number"]
                                .dropna()
                                .astype(str)
                                .tolist()
                            )
                        else:
                            processed = set(df_prev["Part Number"].dropna().astype(str).tolist())
                pre_count = len(processed)
                if pre_count:
                    console.print(
                        "[cyan]Resume enabled: loaded "
                        f"{pre_count} already processed items from {output_csv}[/cyan]"
                    )
            except Exception as e:
                console.print(
                    "[yellow]Resume warning: failed to load existing output for resume: "
                    f"{mask_secrets(str(e))}[/yellow]"
                )
        count = 0

        async def run_all() -> None:
            import aiohttp as _aiohttp
            # Use proper SSL context handling
            ssl_context: Any = None if config.verify_ssl else False
            connector = _aiohttp.TCPConnector(ssl=ssl_context)
            # Create proxy auth only if proxy credentials are available
            proxy_auth = None
            proxy_url_to_use = None
            if config.proxy_username and config.proxy_password and config.proxy_url:
                proxy_auth = _aiohttp.BasicAuth(config.proxy_username, config.proxy_password)
                proxy_url_to_use = config.proxy_url
                console.print(f"[green]🔗 Using proxy: {config.proxy_host} (authenticated)[/green]")
            else:
                console.print("[yellow]⚠️  Running without proxy - direct connection[/yellow]")
            # Add timeout to prevent hanging connections (30s total, 10s connect)
            timeout = _aiohttp.ClientTimeout(total=30, connect=10)
            async with _aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                progress = Progress()
                overall_task_id = progress.add_task("Overall", total=total_items)
                chunk_task_id = progress.add_task("Chunk", total=config.chunksize)
                nonlocal count
                with progress:
                    for raw_chunk in read_part_numbers_in_chunks(input_csv, config.chunksize):
                        # Validate/filter chunk
                        chunk: list[str] = []
                        skipped_existing = 0
                        for pn in raw_chunk:
                            if is_valid_part_number(pn):
                                if pn in processed:
                                    skipped_existing += 1
                                    continue
                                chunk.append(pn)
                            else:
                                console.print(
                                    f"[yellow]Warning: Skipping invalid part number: {pn}[/yellow]"
                                )
                        if not chunk:
                            continue
                        if skipped_existing:
                            console.print(
                                "[cyan]Resume: skipped "
                                f"{skipped_existing} already-processed items in this chunk[/cyan]"
                            )

                        results: list[dict[str, str]] = []
                        progress.reset(chunk_task_id, total=len(chunk))

                        tasks = [
                            process_part_number_generic(
                                session,
                                pn,
                                client_config,
                                semaphore,
                                proxy_url=proxy_url_to_use,
                                proxy_auth=proxy_auth,
                                request_delay_s=config.request_delay_s,
                            )
                            for pn in chunk
                        ]
                        chunk_counter = 0
                        for coro in asyncio.as_completed(tasks):
                            try:
                                result = await coro
                            except Exception as exc:  # safety net
                                safe_msg = mask_secrets(str(exc))
                                console.print(f"[red]Error processing part: {safe_msg}[/red]")
                                progress.advance(chunk_task_id)
                                if total_items is not None:
                                    progress.advance(overall_task_id)
                                chunk_counter += 1
                                count += 1
                                continue
                            chunk_counter += 1
                            count += 1
                            if isinstance(result, dict):
                                results.append(result)

                            # Per-item line output
                            pn = result.get("Part Number", "")
                            status = result.get("Status", "")
                            price = result.get("Price", "N/A")
                            montreal = result.get("Montreal", "N/A")
                            mississauga = result.get("Mississauga", "N/A")
                            edmonton = result.get("Edmonton", "N/A")
                            in_stock = result.get("In Stock", "N/A")
                            # Print per-item output inside progress (as before)
                            console.print(
                                "[white]"
                                f"[{chunk_counter}/{len(chunk)}][{count}/{total_items or '?'}] "
                                "[/white]"
                                f"[yellow]Processed:[/yellow] "
                                f"[bold blue]{mask_secrets(str(pn))}[/bold blue] "
                                f"[magenta]Status:[/magenta] {mask_secrets(str(status))} "
                                f"[green]Price:[/green] {mask_secrets(str(price))} "
                                f"[cyan]Montreal:[/cyan] {mask_secrets(str(montreal))} "
                                f"[cyan]Mississauga:[/cyan] {mask_secrets(str(mississauga))} "
                                f"[cyan]Edmonton:[/cyan] {mask_secrets(str(edmonton))} "
                                f"[blue]In Stock:[/blue] {mask_secrets(str(in_stock))}"
                            )
                            # Also print per-item output outside the progress context so it persists
                            print(
                                f"[{chunk_counter}/{len(chunk)}][{count}/{total_items or '?'}] "
                                f"Processed: {mask_secrets(str(pn))} "
                                f"Status: {mask_secrets(str(status))} "
                                f"Price: {mask_secrets(str(price))} "
                                f"Montreal: {mask_secrets(str(montreal))} "
                                f"Mississauga: {mask_secrets(str(mississauga))} "
                                f"Edmonton: {mask_secrets(str(edmonton))} "
                                f"In Stock: {mask_secrets(str(in_stock))}"
                            )
                            progress.advance(chunk_task_id)
                            if total_items is not None:
                                progress.advance(overall_task_id)

                        # Deduplicate and accumulate
                        unique_results = [
                            r for r in results if r.get("Part Number") not in processed
                        ]
                        new_pns = [
                            r["Part Number"]
                            for r in unique_results
                            if isinstance(r.get("Part Number"), str)
                            and r.get("Part Number")
                        ]
                        processed.update(new_pns)
                        all_results.extend(unique_results)

                        # Save results incrementally (cumulative)
                        if not dry_run:
                            if output_format == OutputFormat.csv:
                                save_results_atomic(output_csv, all_results, client_config.output_columns)
                            elif output_format == OutputFormat.json:
                                with open(output_csv, "w", encoding="utf-8") as f:
                                    json.dump(all_results, f, ensure_ascii=False, indent=2)
                            elif output_format == OutputFormat.excel:
                                df = pd.DataFrame(all_results)
                                df.to_excel(output_csv, index=False)

                        elapsed = time.time() - start_time
                        console.print(
                            "[green]"
                            + mask_secrets(
                                "Processed "
                                f"{count} items so far. Elapsed time: {elapsed:.2f} seconds."
                            )
                            + "[/green]"
                        )

        asyncio.run(run_all())

        summary = generate_summary_report(
            all_results,
            time.time() - start_time,
            input_file=input_csv,
            output_file=output_csv
        )
        safe_summary = mask_secrets(str(summary))
        console.print(f"[bold green]{safe_summary}[/bold green]")

        # Print summary table using rich.table
        table = Table(title="Scrape Summary", show_lines=True)
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")
        status_counts = {
            "Success": len([r for r in all_results if r.get("Status") == "Success"]),
            "Failed": len(
                [
                    r
                    for r in all_results
                    if r.get("Status") in {"Failed", "FetchError", "Error"}
                ]
            ),
            "Not Found": len(
                [
                    r
                    for r in all_results
                    if r.get("Status") in {"Not Found", "No Exact Match"}
                ]
            ),
            "Total": len(all_results),
        }
        for status, c in status_counts.items():
            table.add_row(status, str(c))
        console.print(table)

        # Print summary of failed/skipped items
        failed = [
            r for r in all_results if r.get("Status") in {"Failed", "FetchError", "Error"}
        ]
        not_found = [
            r for r in all_results if r.get("Status") in {"Not Found", "No Exact Match"}
        ]
        if failed:
            console.print(f"[red]Failed items ({len(failed)}):[/red]")
            for r in failed:
                pn = mask_secrets(str(r.get("Part Number", "")))
                err = mask_secrets(str(r.get("Error", r.get("Status", "Unknown error"))))
                console.print(f"  [bold blue]{pn}[/bold blue]: {err}")
        if not_found:
            console.print(f"[yellow]Not found or no exact match ({len(not_found)}):[/yellow]")
            for r in not_found:
                pn = mask_secrets(str(r.get("Part Number", "")))
                status = mask_secrets(str(r.get("Status", "")))
                console.print(f"  [bold blue]{pn}[/bold blue]: {status}")
        try:
            if not dry_run and config.email_notifications_enabled:
                send_email(
                    subject="Generic Scraper - Process Completed",
                    body=safe_summary,
                    to=config.email_notify_to
                )
                console.print("[green]Notification email sent.[/green]")
            elif not dry_run and not config.email_notifications_enabled:
                console.print("[dim]Email notifications disabled.[/dim]")
        except Exception as e:
            safe_msg = mask_secrets(str(e))
            console.print(f"[yellow]Failed to send notification email: {safe_msg}[/yellow]")
    except KeyboardInterrupt:
        console.print(
            "[yellow]\nInterrupted by user. Partial results saved (if not dry-run).[/yellow]"
        )
        # Ensure all_results is always defined
        if not dry_run:
            try:
                save_results_atomic(output_csv, all_results, client_config.output_columns)
            except Exception:
                pass
    # Let Typer handle normal exit

if __name__ == "__main__":
    app()
