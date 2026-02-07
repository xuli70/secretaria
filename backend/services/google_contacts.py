from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def _get_service(creds: Credentials):
    return build("people", "v1", credentials=creds)


def list_contacts(
    creds: Credentials,
    query: str = "",
    max_results: int = 50,
) -> list[dict]:
    service = _get_service(creds)

    if query:
        return search_contacts(creds, query, max_results)

    result = (
        service.people()
        .connections()
        .list(
            resourceName="people/me",
            pageSize=min(max_results, 1000),
            personFields="names,emailAddresses,phoneNumbers,photos",
            sortOrder="LAST_MODIFIED_DESCENDING",
        )
        .execute()
    )
    return [_format_contact(p) for p in result.get("connections", []) if _has_email(p)]


def search_contacts(
    creds: Credentials,
    query: str,
    max_results: int = 20,
) -> list[dict]:
    service = _get_service(creds)
    result = (
        service.people()
        .searchContacts(
            query=query,
            pageSize=min(max_results, 30),
            readMask="names,emailAddresses,phoneNumbers,photos",
        )
        .execute()
    )
    contacts = []
    for item in result.get("results", []):
        person = item.get("person", {})
        if _has_email(person):
            contacts.append(_format_contact(person))
    return contacts


def get_contact(creds: Credentials, resource_name: str) -> dict:
    service = _get_service(creds)
    person = (
        service.people()
        .get(
            resourceName=resource_name,
            personFields="names,emailAddresses,phoneNumbers,photos,organizations",
        )
        .execute()
    )
    return _format_contact(person)


def _has_email(person: dict) -> bool:
    return bool(person.get("emailAddresses"))


def _format_contact(person: dict) -> dict:
    names = person.get("names", [])
    name = names[0].get("displayName", "") if names else ""

    emails = person.get("emailAddresses", [])
    email = emails[0].get("value", "") if emails else ""
    all_emails = [e.get("value", "") for e in emails]

    phones = person.get("phoneNumbers", [])
    phone = phones[0].get("value", "") if phones else ""

    photos = person.get("photos", [])
    photo_url = ""
    if photos and not photos[0].get("default", False):
        photo_url = photos[0].get("url", "")

    resource_name = person.get("resourceName", "")

    return {
        "id": resource_name,
        "name": name,
        "email": email,
        "emails": all_emails,
        "phone": phone,
        "photo": photo_url,
    }
