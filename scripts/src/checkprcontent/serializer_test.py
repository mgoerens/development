from serializer import (
    ContentInfo,
    ReportInfo,
    SourceInfo,
    PRInfo,
)

# In "pre-check" job
# Populate PR Content Info
ci = ContentInfo(
    modified_files=["hello", "world"],
    category="community",
    organization="redhat",
    version="1.42.0",
    chart_name="my_chart",
    web_catalog_only=False,
    report_info=ReportInfo(
        is_provided=True,
        is_signed=False,
        path="my_path",
    ),
    source_info=SourceInfo(
        is_provided=True,
        path="my_path",
    ),
    pr_info=PRInfo(api_url="my_api_url", PRID=42),
)

# Convert to JSON and write to file
ci.dump_content_info("test.json")

# In next job / step
# Load PR Content information
ci2 = ContentInfo.load_content_info("test.json")

# Test printing, accessing information
import pprint

pprint.pprint(ci2)
print(ci2.organization)

print(ci == ci2)  # True
