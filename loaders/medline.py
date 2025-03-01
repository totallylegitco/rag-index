import asyncio
import os

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import concat_ws

from .loader_utils import *
from .medline_schema import medline_schema
from .rag_datasource import *


class MedlineDataSource(RecursiveDataSource):
    flattern = True
    input_options = {
        "rowTag": "PubmedArticle",
        "rootTag": "PubmedArticleSet",
    }
    schema = medline_schema
    input_format = "com.databricks.spark.xml"
    directory_name = "recursive_medline"
    match_condition = "*.xml.gz"
    name = "medline"

    @property
    def urls(self) -> list[str]:
        # If we've running the mini pipeline
        if os.getenv("TESTING_MINI_PIPELINE"):
            return [
                "https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/pubmed25n1275.xml.gz",
            ]
        return [
            "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/",
            "https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/",
        ]

    async def _select(self, df: DataFrame) -> DataFrame:
        await asyncio.sleep(0)
        print(f"Selecting the relevant components...")
        selected = df.select(
            concat_ws(
                " ",
                df["MedlineCitation"]["Article"]["Abstract"]["AbstractText"]["_VALUE"],
            ).alias("text"),
            df["MedlineCitation"]["PMID"].alias("medline_pmid"),
            df["MedlineCitation"]["Article"]["Journal"]["Title"].alias(
                "medline_journal_title"
            ),
            df["MedlineCitation"]["Article"]["ArticleTitle"].alias(
                "medline_article_title"
            ),
            df["MedlineCitation"]["NumberOfReferences"].alias("medline_num_refs"),
            df["MedlineCitation"]["OtherAbstract"].alias("medline_alt_abstract"),
            df["PubmedData"]["ArticleIdList"].alias(
                "pubmed_article_ids"
            ),  # doi, pmedid
        )
        print("Loaded the medline data:")
        selected.show()
        print("Huzzah!")
        return selected
