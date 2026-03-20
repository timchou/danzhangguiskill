#!/usr/bin/env python3

import argparse
import json
import os
from urllib import error, request


def _resolve_value(cli_value, env_name):
    return (cli_value or os.environ.get(env_name, "")).strip()


def _read_chat_content(args):
    if args.chat_content:
        return args.chat_content.strip()
    if args.chat_file:
        with open(args.chat_file, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    return ""


def _read_prefilled_fields(args):
    raw_json = (args.prefilled_fields_json or "").strip()
    if raw_json:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise SystemExit("prefilled_fields_json 不是合法 JSON。") from exc
    elif args.prefilled_fields_file:
        with open(args.prefilled_fields_file, "r", encoding="utf-8") as handle:
            try:
                payload = json.load(handle)
            except json.JSONDecodeError as exc:
                raise SystemExit("prefilled_fields_file 里的内容不是合法 JSON。") from exc
    else:
        return {}

    if not isinstance(payload, dict):
        raise SystemExit("prefilled_fields 必须是 JSON 对象。")
    return payload


def _build_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _send_json_request(*, url, token, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url=url,
        data=body,
        headers=_build_headers(token),
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            response_body = response.read().decode("utf-8")
            return response.status, json.loads(response_body)
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8")
        try:
            payload = json.loads(response_body)
        except json.JSONDecodeError:
            payload = {"ok": False, "error": response_body or f"HTTP {exc.code}"}
        return exc.code, payload


def create_order_draft(args):
    base_url = _resolve_value(args.base_url, "DAN_ERP_BASE_URL").rstrip("/")
    token = _resolve_value(args.token, "DAN_ERP_TOKEN")
    chat_content = _read_chat_content(args)
    prefilled_fields = _read_prefilled_fields(args)

    if not base_url:
        raise SystemExit("缺少 API 地址。请在 Skill 配置里填写 DAN_ERP_BASE_URL，或显式传 --base-url。")
    if not token:
        raise SystemExit("缺少 Token。请在 Skill 配置里填写 DAN_ERP_TOKEN，或显式传 --token。")
    if not chat_content:
        raise SystemExit("缺少聊天内容。可传 --chat-content 或 --chat-file。")

    status_code, payload = _send_json_request(
        url=f"{base_url}/api/order-drafts/",
        token=token,
        payload={
            "chat_content": chat_content,
            "prefilled_fields": prefilled_fields,
            "parse_context": {
                "source": (args.parse_source or "qclaw").strip(),
                "mode": (args.parse_mode or "partial_extract").strip(),
            },
            "client_request_id": (args.client_request_id or "").strip(),
            "client_name": (args.client_name or "").strip(),
        },
    )
    print(json.dumps({"status_code": status_code, "response": payload}, ensure_ascii=False, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description="Dan ERP open API helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-order-draft", help="创建订单草稿")
    create_parser.add_argument("--base-url", default="", help="Dan ERP base URL，默认读取 DAN_ERP_BASE_URL")
    create_parser.add_argument("--token", default="", help="商户 API token，默认读取 DAN_ERP_TOKEN")
    create_parser.add_argument("--chat-content", default="", help="聊天内容")
    create_parser.add_argument("--chat-file", default="", help="从文件读取聊天内容")
    create_parser.add_argument("--prefilled-fields-json", default="", help="预解析字段 JSON")
    create_parser.add_argument("--prefilled-fields-file", default="", help="从文件读取预解析字段 JSON")
    create_parser.add_argument("--parse-source", default="qclaw", help="预解析来源，默认 qclaw")
    create_parser.add_argument("--parse-mode", default="partial_extract", help="预解析模式，默认 partial_extract")
    create_parser.add_argument("--client-request-id", default="", help="调用方请求编号")
    create_parser.add_argument("--client-name", default="", help="调用方系统名")
    create_parser.set_defaults(handler=create_order_draft)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
