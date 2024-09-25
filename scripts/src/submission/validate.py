"""
1. Pull all information related to the submitted chart from GitHub. That "comprend" the files that are added/modified by the PR, and information already present in the repo such as the ones present in the OWNERS file
2. Validate the Submission: Check that the chart/version is not already present in the helm index, validate the web_catalog_only information are correct, validate that the version is semver compatible, validate that the required files are present, ...
3. Save the submission object to a file.

"""

import argparse
import json
import sys

from submission import submission, serializer
from tools import gitutils


def write_submission_to_file(s: submission.Submission, artifact_path: str):
    data = serializer.SubmissionEncoder().encode(s)

    with open(artifact_path, "w") as f:
        f.write(data)


def read_submission_from_file(articact_path: str):
    with open(articact_path, "r") as f:
        s = json.load(f, cls=serializer.SubmissionDecoder)

    return s


def craft_pr_content_error_msg(s: submission.Submission, repository: str):
    # Checks that this PR is a valid "Chart certification" PR
    is_valid, msg = s.is_valid_certification_submission(ignore_owners=True)
    if not is_valid:
        return msg

    # Parse the modified files and determine if it is a "web_catalog_only" certification
    try:
        s.parse_web_catalog_only(repo_path="pr-branch")
    except submission.SubmissionError as e:
        return str(e)

    if s.is_web_catalog_only:
        is_valid, msg = s.is_valid_web_catalog_only(repo_path="pr-branch")
        if not is_valid:
            return msg

    index = submission.download_index_data(repository)
    try:
        s.chart.check_index(index)
    except submission.HelmIndexError as e:
        return str(e)

    try:
        s.chart.check_release_tag(repository)
    except submission.ReleaseTagError as e:
        return str(e)

    return ""


def craft_owners_error_msg(s):
    is_valid, msg = s.is_valid_owners_submission()
    if is_valid:
        if s.chart.category == "partners":
            msg = "[ERROR] OWNERS file should never be set directly by partners. See certification docs."
        else:
            msg = "[INFO] OWNERS file changes require manual review by maintainers."
    return msg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--api_url",
        dest="api_url",
        type=str,
        required=True,
        help="API URL for the pull request",
    )
    parser.add_argument(
        "-r",
        "--repository",
        dest="repository",
        type=str,
        required=True,
        help="Git Repository",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        required=True,
        help="Path to artifact file to write Submission json representation",
    )

    args = parser.parse_args()
    s = submission.Submission(args.api_url)
    try:
        s.parse_modified_files()
    except submission.SubmissionError as e:
        write_submission_to_file(s, args.output)
        print(str(e))
        gitutils.add_output("pr-content-error-message", str(e))
        sys.exit(10)

    owners_error_msg = ""
    if s.modified_owners:
        # If the PR contains an OWNER file, craft a error message to be added as a comment in the PR
        owners_error_msg = craft_owners_error_msg(s)
        print(owners_error_msg)
        gitutils.add_output("owners-error-message", owners_error_msg)

    pr_content_error_msg = craft_pr_content_error_msg(s, args.repository)
    if pr_content_error_msg:
        print(pr_content_error_msg)
        gitutils.add_output("pr-content-error-message", pr_content_error_msg)

    # Some subsequent steps require those github outputs
    gitutils.add_output("chart_entry_name", s.chart.name)
    gitutils.add_output("release_tag", s.chart.get_release_tag())
    gitutils.add_output("web_catalog_only", s.is_web_catalog_only)
    gitutils.add_output("vendor_type", s.chart.get_vendor_type())

    write_submission_to_file(s, args.output)

    if owners_error_msg or pr_content_error_msg:
        print(
            f"exit with owners_error_msg={owners_error_msg}; pr_content_error_msg={pr_content_error_msg}"
        )
        sys.exit(20)


if __name__ == "__main__":
    main()
