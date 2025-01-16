"""
Lambda function to fetch Freshdesk tickets that have been created
or updated in the past day and save them to S3
"""

import base64
import json
import logging
import os

from datetime import datetime, timedelta

import boto3
import requests

logger = logging.getLogger()
logger.setLevel("INFO")

# Env vars
FRESHDESK_DOMAIN = os.environ.get("FRESHDESK_DOMAIN")
FRESHDESK_API_KEY_PARAMETER_NAME = os.environ.get("FRESHDESK_API_KEY_PARAMETER_NAME")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
S3_OBJECT_PREFIX = os.environ.get("S3_OBJECT_PREFIX")

# Label lookups
SOURCE_LOOKUP = {
    1: "Email",
    2: "Portal",
    3: "Phone",
    7: "Chat",
    9: "Feedback Widget",
    10: "Outbound Email",
}

STATUS_LOOKUP = {
    2: "Open",
    3: "Pending",
    4: "Resolved",
    5: "Closed",
    6: "Waiting on Customer",
    7: "Waiting on Third Party",
}

PRIORITY_LOOKUP = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}

CONVERSATION_REPLY = 0
CONVERSATION_NOTE = 2
CONVERSATION_SOURCE = {
    CONVERSATION_REPLY: "Reply",
    CONVERSATION_NOTE: "Note",
}


class FreshdeskClient:
    """Client to interact with Freshdesk API"""

    def __init__(self, domain, api_key):
        """Initialize client with domain, api_key and headers"""
        self.base_url = f"https://{domain}"
        self.encoded_key = base64.b64encode(f"{api_key}:X".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.encoded_key}",
            "Content-Type": "application/json",
        }
        self.products_cache = self.get_products()
        self.contacts_cache = {}

    def get_products(self):
        logger.info("Fetching products from API...")
        products = {}
        url = f"{self.base_url}/api/v2/products"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            products = {
                str(product["id"]): product["name"] for product in response.json()
            }
        else:
            logger.info(f"Error fetching products: {response.status_code}")
        return products

    def get_ticket_conversations(self, ticket_id):
        """Fetch all ticket conversations"""
        logger.info(f"Fetching conversations from API for {ticket_id}...")
        page = 1
        per_page = 100
        reply_count = 0
        note_count = 0
        while page <= 10:  # Limit to 1000 conversations
            url = f"{self.base_url}/api/v2/tickets/{ticket_id}/conversations?per_page={per_page}&page={page}"
            response = requests.get(url, headers=self.headers)
            try:
                response.raise_for_status()
                conversations = response.json()
                reply_count += len(
                    [c for c in conversations if c.get("source") == CONVERSATION_REPLY]
                )
                note_count += len(
                    [c for c in conversations if c.get("source") == CONVERSATION_NOTE]
                )
                if len(conversations) == per_page:
                    page += 1
                else:
                    break
            except requests.exceptions.HTTPError as e:
                logger.error(f"Error fetching conversations: {e}")
                break
        return {
            "total_count": reply_count + note_count,
            "reply_count": reply_count,
            "note_count": note_count,
        }

    def get_requester_email_suffix(self, requester_id):
        """Get contact's email type (internal/external) using in-memory cache"""
        if str(requester_id) not in self.contacts_cache:
            logger.info(f"Fetching contact {requester_id} from API...")
            url = f"{self.base_url}/api/v2/contacts/{requester_id}"
            response = requests.get(url, headers=self.headers)
            try:
                response.raise_for_status()
                contact = response.json()
                email = contact.get("email", "").lower()

                # Check email suffix
                internal_domains = ["cds-snc.ca", "canada.ca"]
                email_suffix = email.split("@")[-1]
                if email_suffix in internal_domains or email_suffix.endswith(".gc.ca"):
                    suffix = email_suffix
                else:
                    suffix = "external"
                self.contacts_cache[str(requester_id)] = suffix
            except requests.exceptions.HTTPError as e:
                if response.status_code == 404:
                    logger.warning(f"Contact {requester_id} not found")
                else:
                    logger.error(f"Error fetching contact: {e}")
                self.contacts_cache[str(requester_id)] = "unknown"
        return self.contacts_cache[str(requester_id)]

    def get_tickets(self):
        """Retrieve all tickets with product names and requester email types"""
        all_tickets = []
        yesterday = datetime.now() - timedelta(days=1)
        page = 1
        per_page = 30  # set by the API
        while page <= 10:  # API limit of 10 pages
            url = f"{self.base_url}/api/v2/search/tickets?query=\"updated_at:'{yesterday.strftime('%Y-%m-%d')}'\"&page={page}"
            response = requests.get(url, headers=self.headers)
            try:
                response.raise_for_status()
                tickets = response.json()
                for ticket in tickets.get("results", []):
                    status_num = ticket.get("status")
                    priority_num = ticket.get("priority")
                    source_num = ticket.get("source")
                    product_id = ticket.get("product_id")
                    requester_id = ticket.get("requester_id")
                    custom_fields = ticket.get("custom_fields", {})
                    conversations = self.get_ticket_conversations(ticket.get("id"))

                    filtered_ticket = {
                        "id": ticket.get("id"),
                        "status": status_num,
                        "status_label": STATUS_LOOKUP.get(status_num, "Unknown"),
                        "priority": priority_num,
                        "priority_label": PRIORITY_LOOKUP.get(priority_num, "Unknown"),
                        "source": source_num,
                        "source_label": SOURCE_LOOKUP.get(source_num, "Unknown"),
                        "created_at": ticket.get("created_at"),
                        "updated_at": ticket.get("updated_at"),
                        "due_by": ticket.get("due_by"),
                        "fr_due_by": ticket.get("fr_due_by"),
                        "is_escalated": ticket.get("is_escalated"),
                        "tags": ticket.get("tags", []),
                        "spam": ticket.get("spam", False),
                        "requester_email_suffix": self.get_requester_email_suffix(
                            requester_id
                        ),
                        "type": ticket.get("type"),
                        "product_id": product_id,
                        "product_name": self.products_cache.get(
                            str(product_id), "Unknown"
                        ),
                        "conversations_total_count": conversations.get("total_count"),
                        "conversations_reply_count": conversations.get("reply_count"),
                        "conversations_note_count": conversations.get("note_count"),
                        "language": custom_fields.get("cf_language"),
                        "province_or_territory": custom_fields.get(
                            "cf_provinceterritory"
                        ),
                        "organization": custom_fields.get("cf_organization"),
                    }
                    all_tickets.append(filtered_ticket)

                # Check if there are more tickets to fetch
                if len(tickets.get("results", [])) == per_page:
                    logger.info(f"Fetching page {page + 1}...")
                    page += 1
                else:
                    logger.info("All tickets fetched")
                    break
            except requests.exceptions.HTTPError as e:
                logger.error(f"Error fetching tickets: {e}")
                break

        return all_tickets


def upload_to_s3(bucket, prefix, data):
    """Upload data to S3 bucket"""
    s3_client = boto3.client("s3")

    yesterday = datetime.now() - timedelta(days=1)
    day = yesterday.strftime("%Y-%m-%d")
    month = yesterday.strftime("%Y-%m")
    key = f"{prefix}/MONTH={month}/{day}.json"

    s3_client.put_object(
        Bucket=bucket, Key=key, Body=json.dumps(data, ensure_ascii=False)
    )
    return f"s3://{bucket}/{key}"


def get_ssm_parameter(parameter_name):
    """Get parameter value from SSM Parameter Store"""
    ssm_client = boto3.client("ssm")
    try:
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except ssm_client.exceptions.ParameterNotFound:
        logger.error(f"SSM parameter '{parameter_name}' not found")
        raise ValueError(f"SSM parameter '{parameter_name}' not found")


def handler(_event, _context):
    """Lambda handler to fetch tickets and save them to S3"""
    freshdesk_api_key = get_ssm_parameter(FRESHDESK_API_KEY_PARAMETER_NAME)

    logger.info("Fetching tickets...")
    client = FreshdeskClient(FRESHDESK_DOMAIN, freshdesk_api_key)
    tickets = client.get_tickets()

    if tickets:
        logger.info(f"Saving {len(tickets)} tickets")
        s3_path = upload_to_s3(S3_BUCKET_NAME, S3_OBJECT_PREFIX, tickets)
        logger.info(f"Tickets saved to {s3_path}")
    else:
        logger.info("No tickets found")
