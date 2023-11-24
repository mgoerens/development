import json
import copy

from dataclasses import dataclass
from typing import Literal


@dataclass
class ReportInfo:
    is_provided: bool
    is_signed: bool
    path: str


@dataclass
class SourceInfo:
    is_provided: bool
    path: str


@dataclass
class PRInfo:
    api_url: str
    PRID: int


@dataclass
class ContentInfo:
    modified_files: list[str]
    category: Literal["partners", "community", "redhat"]
    organization: str
    version: str  # semver validation ?
    chart_name: str
    web_catalog_only: bool

    report_info: ReportInfo
    source_info: SourceInfo
    pr_info: PRInfo

    # def get_category_org_name_version_from_files():
    #

    def dump_content_info(self, path):
        """ """

        content_info_str = ContentInfoEncoder().encode(self)
        # import pdb; pdb.set_trace()
        content_info_dict = json.loads(content_info_str)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(content_info_dict, f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_content_info(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f, cls=ContentInfoDecoder)


class ContentInfoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ContentInfo):
            obj_dict = copy.deepcopy(obj.__dict__)
            obj_dict["report_info"] = obj_dict["report_info"].__dict__
            obj_dict["source_info"] = obj_dict["source_info"].__dict__
            obj_dict["pr_info"] = obj_dict["pr_info"].__dict__
            return obj_dict

        return json.JSONEncoder.default(self, obj)


class ContentInfoDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if "report_info" in dct:
            report_info_obj = ReportInfo(**dct["report_info"])
            source_info_obj = SourceInfo(**dct["source_info"])
            pr_info_obj = PRInfo(**dct["pr_info"])

            to_merge_dct = {
                "report_info": report_info_obj,
                "source_info": source_info_obj,
                "pr_info": pr_info_obj,
            }

            new_dct = dct | to_merge_dct
            return ContentInfo(**new_dct)
        return dct
