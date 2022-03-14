import argparse
import csv
import fileinput
import io
import json
from pathlib import Path

from csv import DictReader


def is_float(string):
    try:
        float(string)
    except ValueError:
        return False
    else:
        return True


def extract_data(file_name: str):
    if not Path(file_name).is_file():
        return ("FILE_DOES_NOT_EXIST", file_name)
    header_str = fileinput.input(file_name)[0]
    fileinput.close()
    headers = ["experiment_name", "sample_id", "fauxness", "category_guess"]
    categories = ["real", "fake", "ambiguous"]
    for header in headers:
        if header not in str(header_str):
            return ("INVALID_HEADERS", header_str)

    with open(file_name) as f:
        reader = DictReader(f)
        results = []
        for row in reader:
            if len(row["experiment_name"]) == 0:
                return ("EMPTY_EXPERIMENT_NAME", row)
            if not row["sample_id"].isdigit():
                return ("SAMPLE_ID_NOT_INT", row["sample_id"])
            row["sample_id"] = int(row["sample_id"])
            if row["sample_id"] < 0:
                return ("SAMPLE_ID_NEGATIVE", row)
            if not is_float(row["fauxness"]):
                return ("FAUXNESS_NOT_FLOAT", row)
            row["fauxness"] = float(row["fauxness"])
            if row["fauxness"] < 0 or row["fauxness"] > 1.0:
                return ("FAUXNESS_OUT_OF_RANGE", row)
            if row["category_guess"] not in categories:
                return ("INVALID_CATEGORY_GUESS", row)
            results.append(row)
    if len(results) == 0:
        return ("NO_DATA", results)
    return ("SUCCESS", results)


def generate_summary(return_code, payload):
    result = {}
    if return_code == "SUCCESS":
        fauxnesses = sorted([x["fauxness"] for x in payload])
        if len(fauxnesses) == 1:
            min_fauxness = max_fauxness = fauxnesses[0]
        else:
            min_fauxness = fauxnesses[0]
            max_fauxness = fauxnesses[-1]
        result = {
            "return_code": return_code,
            "payload": "",
            "extras": {
                "rows": len(payload),
                "fauxness_range": (min_fauxness, max_fauxness),
            },
        }
    else:
        result = {"return_code": return_code, "payload": payload, "extras": {}}
    return json.dumps(result)


def fetch_row(payload, row_num, format=None):
    result = payload[row_num]
    if format == "JSON":
        return json.dumps(result)
    elif format == "CSV":
        output = io.StringIO()
        writer = csv.DictWriter(output, result.keys(), quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        writer.writerow(result)
        return output.getvalue()
    else:
        return result


def test():
    return_code, payload = extract_data("file_0.faux")
    summary = generate_summary(return_code, payload)

    print(fetch_row(payload, 0, "JSON"))
    print(fetch_row(payload, 0, "CSV"))
    print(fetch_row(payload, 0, "PYTHON"))

    print("file_0", summary)
    return_code, payload = extract_data("file_1.faux")
    summary = generate_summary(return_code, payload)
    json_summary = json.dumps(summary)
    print("file_1", json_summary)

    return_code, payload = extract_data("file_3.faux")
    summary = generate_summary(return_code, payload)
    print("file_3", summary)

    return_code, payload = extract_data("file_4.faux")
    summary = generate_summary(return_code, payload)
    print("file_4", summary)

    return_code, payload = extract_data("file_5.faux")
    summary = generate_summary(return_code, payload)
    print("file_5", summary)

    return_code, payload = extract_data("file_6.faux")
    summary = generate_summary(return_code, payload)
    print("file_6", summary)

    return_code, payload = extract_data("file_7.faux")
    summary = generate_summary(return_code, payload)
    print("file_7", summary)

    return_code, payload = extract_data("file_9.faux")
    summary = generate_summary(return_code, payload)
    print("file_9", summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", type=str, help="Fauxlizer csv data file.")
    parser.add_argument(
        "-f", "--format", type=str, help="Output format. Arguments can be JSON or CSV"
    )
    parser.add_argument(
        "-l", "--linenum", type=int, help="Line number to output"
    )
    args = parser.parse_args()
    return_code, payload = extract_data(args.file_name)
    summary = generate_summary(return_code, payload)
    print(summary)

    if args.linenum is not None and return_code == "SUCCESS":
        if args.linenum > len(payload):
            print("Invalid argument for line number.")
        else:
            row = fetch_row(payload, args.linenum, format=args.format)
            print(row)
