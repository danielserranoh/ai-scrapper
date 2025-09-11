#!/usr/bin/env python3
"""
University Web Crawler - Main CLI Interface
"""

import click
import logging
import sys
from pathlib import Path

from config import get_config, LOG_CONFIG
from pipeline.manager import PipelineManager
from storage.data_store import DataStore
from utils.common import format_duration, format_bytes


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    LOG_CONFIG.ensure_directory()
    
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logger = logging.getLogger()
    
    # Only setup if not already configured
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create formatters
        file_formatter = logging.Formatter(LOG_CONFIG.format)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        # File handler
        file_handler = logging.FileHandler(LOG_CONFIG.file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    else:
        # Just update the level if already configured
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)


@click.command()
@click.argument('domain')
@click.option('--job-id', help='Custom job ID')
@click.option('--delay', type=float, help='Base delay between requests (seconds)')
@click.option('--max-pages', type=int, help='Maximum pages to crawl')
@click.option('--timeout', type=int, help='Maximum crawl time (hours)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def crawl(domain, job_id, delay, max_pages, timeout, verbose):
    """Start a new crawl job for DOMAIN"""
    if verbose:
        setup_logging(verbose=True)
    
    config = get_config(domain)
    
    # Apply command-line overrides
    if delay:
        config.base_delay = delay
    if max_pages:
        config.max_pages = max_pages
    if timeout:
        config.timeout_hours = timeout
    
    manager = PipelineManager(config)
    
    try:
        job = manager.start_new_job(domain, job_id)
        click.echo(f"Started job {job.job_id} for domain {domain}")
        
        success = manager.run_pipeline(timeout)
        
        if success:
            click.echo(f"✅ Job {job.job_id} completed successfully")
            
            # Show summary
            status = manager.get_job_status()
            if status:
                click.echo(f"  📊 Processed: {status['processed_pages']} pages")
                click.echo(f"  ❌ Failed: {status['failed_pages']} pages")
                click.echo(f"  ⏱️  Duration: {format_duration(status.get('elapsed_seconds', 0))}")
        else:
            click.echo(f"❌ Job {job.job_id} failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo("\n🛑 Crawl interrupted by user")
        manager.pause_job()
        click.echo(f"Job {manager.current_job.job_id if manager.current_job else 'unknown'} paused. Use resume command to continue.")
        
    except Exception as e:
        click.echo(f"❌ Crawl failed: {e}")
        logging.exception("Crawl failed")
        sys.exit(1)


@click.command()
@click.argument('job_id')
@click.option('--timeout', type=int, help='Maximum additional time (hours)')
def resume(job_id, timeout):
    """Resume a paused job"""
    config = get_config()
    manager = PipelineManager(config)
    
    try:
        job = manager.resume_job(job_id)
        if not job:
            click.echo(f"❌ Job {job_id} not found")
            sys.exit(1)
        
        click.echo(f"🔄 Resuming job {job.job_id} for domain {job.domain}")
        
        success = manager.run_pipeline(timeout)
        
        if success:
            click.echo(f"✅ Job {job.job_id} completed successfully")
        else:
            click.echo(f"❌ Job {job.job_id} failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo("\n🛑 Resume interrupted by user")
        manager.pause_job()
        
    except Exception as e:
        click.echo(f"❌ Resume failed: {e}")
        logging.exception("Resume failed")
        sys.exit(1)


@click.command()
@click.argument('job_id', required=False)
def status(job_id):
    """Show job status. Use 'current' for running job or omit for all jobs."""
    config = get_config()
    manager = PipelineManager(config)
    
    if job_id:
        # Show specific job status
        if job_id == 'current' and manager.current_job:
            status = manager.get_job_status()
        else:
            from storage.checkpoints import CheckpointManager
            checkpoint_manager = CheckpointManager()
            status = checkpoint_manager.get_job_status(job_id)
        
        if not status:
            click.echo(f"❌ Job {job_id} not found")
            sys.exit(1)
        
        click.echo(f"📋 Job Status: {job_id}")
        click.echo(f"  🌐 Domain: {status['domain']}")
        click.echo(f"  📊 Status: {status['status']}")
        click.echo(f"  📈 Stage: {status.get('current_stage', 'unknown')}")
        click.echo(f"  📄 Total Pages: {status.get('total_pages', 0)}")
        click.echo(f"  ✅ Processed: {status.get('processed_pages', 0)}")
        click.echo(f"  ❌ Failed: {status.get('failed_pages', 0)}")
        
        if 'queue_status' in status:
            queue = status['queue_status']
            click.echo(f"  📝 Queue - Pending: {queue.get('pending', 0)}, "
                      f"Processing: {queue.get('processing', 0)}, "
                      f"Completed: {queue.get('completed', 0)}")
        
        if status.get('last_checkpoint'):
            click.echo(f"  💾 Last Checkpoint: {status['last_checkpoint']}")
    
    else:
        # Show all jobs
        jobs = manager.list_jobs()
        
        if not jobs:
            click.echo("📭 No jobs found")
            return
        
        click.echo("📋 All Jobs:")
        click.echo("="*60)
        for job in jobs:
            status_emoji = {
                'completed': '✅',
                'running': '🔄', 
                'paused': '⏸️',
                'failed': '❌',
                'pending': '⏳'
            }.get(job['status'], '❓')
            
            click.echo(f"{status_emoji} {job['job_id']}")
            click.echo(f"    🌐 {job['domain']} | 📊 {job['status']} | "
                      f"📄 {job.get('total_pages', 0)} pages")


@click.command()
@click.argument('job_id')
@click.option('--format', type=click.Choice(['csv', 'json']), help='Show files of specific format')
def export(job_id, format):
    """Show export files for JOB_ID"""
    data_store = DataStore()
    
    try:
        # Get job files
        files = data_store.get_job_files(job_id)
        
        if not any(files.values()):
            click.echo(f"❌ No export files found for job {job_id}")
            sys.exit(1)
        
        click.echo(f"📁 Export files for job {job_id}:")
        
        for file_type, file_list in files.items():
            if file_list:
                click.echo(f"  {file_type.title()}:")
                for file_path in sorted(file_list):
                    size_bytes = Path(file_path).stat().st_size
                    click.echo(f"    📄 {Path(file_path).name} ({format_bytes(size_bytes)})")
        
        if format:
            # Show latest files of specified format
            latest_files = {}
            for file_type, file_list in files.items():
                if file_list:
                    latest_files[file_type] = max(file_list, key=lambda x: Path(x).stat().st_mtime)
            
            click.echo(f"\n📋 Latest files in {format} format:")
            for file_type, file_path in latest_files.items():
                if format.lower() in file_path.lower():
                    click.echo(f"  {file_type}: {file_path}")
        
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")
        sys.exit(1)


@click.command()
def list_jobs():
    """List all available jobs"""
    from storage.checkpoints import CheckpointManager
    checkpoint_manager = CheckpointManager()
    
    job_ids = checkpoint_manager.list_jobs()
    
    if not job_ids:
        click.echo("📭 No jobs found")
        return
    
    click.echo("📋 Available Jobs:")
    click.echo("="*40)
    
    for job_id in job_ids:
        status = checkpoint_manager.get_job_status(job_id)
        if status:
            status_emoji = {
                'completed': '✅',
                'running': '🔄',
                'paused': '⏸️', 
                'failed': '❌',
                'pending': '⏳'
            }.get(status['status'], '❓')
            
            click.echo(f"{status_emoji} {job_id}")
            click.echo(f"    🌐 {status['domain']}")
            click.echo(f"    📊 {status['status']} | 📄 {status.get('total_pages', 0)} pages")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """University Web Crawler - Business Intelligence Tool
    
    Examples:
      crawl harvard.edu                    # Crawl Harvard University
      crawl stanford.edu --delay 2 -v     # Crawl with 2s delay and verbose logging
      resume job_20240101_120000           # Resume paused job  
      status                               # List all jobs
      status job_20240101_120000           # Show job status
      export job_20240101_120000 --format csv  # Show CSV exports
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


# Add commands to the group
cli.add_command(crawl)
cli.add_command(resume)
cli.add_command(status)
cli.add_command(export)
cli.add_command(list_jobs, name='list')


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()