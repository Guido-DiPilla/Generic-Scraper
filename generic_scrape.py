"""Main entry point for the Generic Multi-Client Web Scraper.

Supports running both as a module (python -m generic_scraper.generic_scrape)
and directly as a script (python generic_scraper/generic_scrape.py).
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

# Import shim: allow running as a module or as a script without package context
try:  # Prefer package-relative imports
    from .config import get_config
    from .email_utils import send_email
    from .io_utils import (
        generate_summary_report,
        read_part_numbers_in_chunks,
        save_results_atomic,
        validate_input_schema,
        validate_output_schema,
    )
    from .log_utils import mask_secrets, setup_logging
    from .generic_scraper import process_part_number_generic
    from .ui import console, select_file
    from .client_config import registry
    from . import clients  # This registers all available clients
    from . import G2S     # This registers G2S client from separate folder
except ImportError:  # Fallback for direct script execution
    from config import get_config
    from email_utils import send_email
    from io_utils import (
        generate_summary_report,
        read_part_numbers_in_chunks,
        save_results_atomic,
        validate_input_schema,
        validate_output_schema,
    )
    from log_utils import mask_secrets, setup_logging
    from generic_scraper import process_part_number_generic
    from ui import console, select_file
    from client_config import registry
    import clients  # This registers all available clients
    import G2S     # This registers G2S client from separate folder

app = typer.Typer()

class OutputFormat(str, Enum):
    csv = "csv"
    json = "json"
    excel = "excel"

def option_wrapper(help_text):
    """Simple wrapper to create options with consistent settings"""
    def decorator(f):
        return typer.Option(f, help=help_text)
    return decorator

@app.command()
def main(
    input_csv: Optional[Path] = option_wrapper("Input CSV file path")(None),
    output_csv: Optional[Path] = option_wrapper("Output file path (CSV/JSON/Excel)")(None),
    client: Optional[str] = option_wrapper("Client ID (e.g., 'g2s'). If not provided, will prompt for selection.")(None),
    log_level: Optional[str] = option_wrapper("Log level (INFO, DEBUG, etc.)")(None),
    dry_run: bool = option_wrapper("Dry run mode (no writes)")(False),
    output_format: OutputFormat = option_wrapper("Output format: csv, json, or excel")(OutputFormat.csv),
    resume: bool = option_wrapper("Resume from existing output by skipping already processed part numbers")(False),
) -> None:
    """Run the Generic Scraper with CLI or interactive mode."""
    config = get_config()
    if log_level:
        config = config.__class__(**{**config.__dict__, 'log_level': log_level})
    
    # Client selection
    client_config = None
    if client:
        client_config = registry.get_client(client)
        if not client_config:
            available_clients = registry.get_client_ids()
            console.print(f"[red]Client '{client}' not found. Available clients: {', '.join(available_clients)}[/red]")
            raise typer.Exit(1)
    else:
        # Interactive client selection
        available_clients = registry.list_clients()
        if not available_clients:
            console.print("[red]No clients are registered. Please check your client configurations.[/red]")
            raise typer.Exit(1)
        elif len(available_clients) == 1:
            client_config = available_clients[0]
            console.print(f"[cyan]Using only available client: {client_config.client_name}[/cyan]")
        else:
            console.print("[bold cyan]Available Scraping Clients:[/bold cyan]")
            for i, cfg in enumerate(available_clients, 1):
                console.print(f"  {i}. {cfg.client_name} ({cfg.client_id}) - {cfg.description}")
            
            while True:
                try:
                    choice = typer.prompt("Select client number")
                    client_idx = int(choice) - 1
                    if 0 <= client_idx < len(available_clients):
                        client_config = available_clients[client_idx]
                        break
                    else:
                        console.print(f"[red]Please enter a number between 1 and {len(available_clients)}[/red]")
                except (ValueError, KeyboardInterrupt):
                    console.print("[red]Invalid selection. Please enter a number.[/red]")
                    
    console.print(f"[green]Selected client: {client_config.client_name}[/green]")

    # Proxy connectivity test (use BasicAuth and proxy_host, not creds in URL)
    import aiohttp
    async def proxy_test() -> None:
            test_url = "https://ipapi.co/json/"  # HTTPS to avoid plaintext
            import random as _random
            attempts = 3
            last_err: str | None = None
            for attempt in range(attempts):
                try:
                    # Use None for default SSL context to satisfy mypy
                    connector = aiohttp.TCPConnector(ssl=None if config.verify_ssl else False)
                    timeout = aiohttp.ClientTimeout(total=10)
                    proxy = f"http://{config.proxy_host}"  # no credentials in URL
                    proxy_auth = aiohttp.BasicAuth(config.proxy_username, config.proxy_password)
                    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                        async with session.get(test_url, proxy=proxy, proxy_auth=proxy_auth) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                console.print(f"[green]Proxy test successful. Details:[/green] {data}")
                                return
                            last_err = f"HTTP status: {resp.status}"
                            raise RuntimeError(last_err)
                except Exception as e:
                    safe = mask_secrets(str(e))
                    last_err = safe if safe else e.__class__.__name__
                    if attempt < attempts - 1:
                        # Exponential backoff with jitter: 1s, 2s, ...
                        delay = (2 ** attempt) + _random.uniform(0, 0.5)
                        await asyncio.sleep(delay)
                        continue
            console.print(f"[red]Proxy test failed after {attempts} attempts: {last_err}[/red]")
    asyncio.run(proxy_test())

    setup_logging(config.log_file, config.log_level)
    console.print("[bold cyan]Generic Multi-Client Web Scraper[/bold cyan]")

    # Use CLI args if provided, else prompt interactively
    if input_csv is None:
        input_csv = select_file("open")
    if output_csv is None:
        output_csv = select_file("save")

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
            # Use None for default SSL context to satisfy mypy
            connector = _aiohttp.TCPConnector(ssl=None if config.verify_ssl else False)
            # Create proxy auth with required credentials
            proxy_auth = _aiohttp.BasicAuth(config.proxy_username, config.proxy_password)
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
                                proxy_url=config.proxy_url,
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
            if not dry_run:
                send_email(
                    subject="Generic Scraper - Process Completed",
                    body=safe_summary,
                    to=config.email_notify_to
                )
                console.print("[green]Notification email sent.[/green]")
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
