import sys
from utils.model_loader import ModelLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from models.model import Metadata
from prompt.prompt_library import PROMPT_REGISTRY
from exceptions.custom_exception import DocumentPortalException
from logger import GLOBAL_LOGGER as log


class DocumentAnalysis:
    "Analyses documents"
    def __init__(self):
        try:
            self.loader = ModelLoader()
            self.llm = self.loader.load_llm()

            self.parser = JsonOutputParser(pydantic_object=Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(self.llm, self.parser)

            self.prompt = PROMPT_REGISTRY["document_analysis"]

            log.info("Document analysis initialized")

        except Exception as e:
            log.error("Failed to initialize document analysis", error=str(e))
            raise DocumentPortalException(f"Failed to initialize document analysis", sys)


    def analyse_document(self, document_text: str) -> dict:

        try:

            chain = self.prompt | self.llm | self.fixing_parser

            log.info("Analysing document")

            response = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                 "document_text": document_text})

            log.info("Document analysed successfully",key=list(response.keys()))

            return response

        except Exception as e:
            log.error("Failed to analyse document", error=str(e))
            raise DocumentPortalException(f"Failed to analyse document: {str(e)}", sys)