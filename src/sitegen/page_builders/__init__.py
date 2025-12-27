# -*- coding: utf-8 -*-
from sitegen.page_builders.page_top import write as write_top
from sitegen.page_builders.page_rules import write as write_rules
from sitegen.page_builders.page_products import write as write_products
from sitegen.page_builders.page_services import write as write_services
from sitegen.page_builders.page_search import write as write_search
from sitegen.page_builders.page_wiki import write as write_wiki
from sitegen.page_builders.page_howto import write as write_howto

__all__ = [
    "write_top",
    "write_rules",
    "write_products",
    "write_services",
    "write_search",
    "write_wiki",
    "write_howto",
]
