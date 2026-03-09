import os
import argparse

from src.config_loader import load_config
from src.llm_client import LLMClient
from src.daily_processor import process_single_pdf
from src.weekly_builder import (
    load_daily_jsons,
    filter_weekly_docs,
    build_weekly_report_text,
    save_weekly_report,
)
from src.outlook_sender import send_outlook_mail


def get_llm_client(config):
    return LLMClient(
        base_url=config["llm"]["base_url"],
        api_key=config["llm"]["api_key"],
        model_text=config["llm"]["model_text"],
        model_vision=config["llm"].get("model_vision", config["llm"]["model_text"]),
        timeout_seconds=config["llm"].get("timeout_seconds", 300),
    )


def process_daily(config):
    input_dir = config["paths"]["input_dir"]
    output_dir = config["paths"]["daily_output_dir"]
    csv_path = config["paths"]["daily_summary_csv"]
    year = config["app"].get("default_year", 2026)
    llm = get_llm_client(config)

    if not os.path.exists(input_dir):
        print(f"[ERROR] input_dir not found: {input_dir}")
        return

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            print(f"[PROCESS] {pdf_path}")
            out = process_single_pdf(pdf_path, llm, output_dir, csv_path, year=year)
            print(f"[DONE] {out}")


def build_weekly(config, week_start: str):
    llm = get_llm_client(config)
    daily_output_dir = config["paths"]["daily_output_dir"]
    weekly_output_dir = config["paths"]["weekly_output_dir"]

    docs = load_daily_jsons(daily_output_dir)
    weekly_docs = filter_weekly_docs(docs, week_start)

    if not weekly_docs:
        print(f"[INFO] no files found for week starting {week_start}")
        return None, None, None

    report_text, weekly_input_data = build_weekly_report_text(llm, week_start, weekly_docs)
    md_path, html_path, ref_md_path, ref_html_path, json_path = save_weekly_report(
        weekly_output_dir, week_start, report_text, weekly_input_data
    )

    print(f"[WEEKLY REPORT MD] {md_path}")
    print(f"[WEEKLY REPORT HTML] {html_path}")
    print(f"[WEEKLY REFERENCE MD] {ref_md_path}")
    print(f"[WEEKLY REFERENCE HTML] {ref_html_path}")
    print(f"[WEEKLY INPUT JSON] {json_path}")

    return md_path, html_path, ref_md_path, ref_html_path, json_path, report_text


def send_weekly(config, week_start: str):
    md_path, ref_md_path, json_path, report_text = build_weekly(config, week_start)
    if not report_text:
        return

    subject_prefix = config["outlook"]["subject_prefix"]
    subject = f"{subject_prefix} ({week_start} 주차)"
    to_list = config["outlook"]["to"]
    cc_list = config["outlook"].get("cc", [])
    mode = config["app"]["send_mode"]

    send_outlook_mail(subject, report_text, to_list, cc_list, mode=mode)
    print(f"[OUTLOOK] mode={mode}, report={md_path}")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("process-daily")

    weekly_parser = subparsers.add_parser("build-weekly")
    weekly_parser.add_argument("--week", required=True, help="주차 시작일(월요일), 예: 2026-01-19")

    send_parser = subparsers.add_parser("send-weekly")
    send_parser.add_argument("--week", required=True, help="주차 시작일(월요일), 예: 2026-01-19")

    args = parser.parse_args()
    config = load_config("config.yaml")

    if args.command == "process-daily":
        process_daily(config)
    elif args.command == "build-weekly":
        build_weekly(config, args.week)
    elif args.command == "send-weekly":
        send_weekly(config, args.week)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()