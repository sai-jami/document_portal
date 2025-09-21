import sys
from dotenv import load_dotenv
from utils.model_loader import ModelLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from logger import GLOBAL_LOGGER as log
from prompt.prompt_library import PROMPT_REGISTRY
from models.model import PromptType,SummaryResponse



class DocumentComparatorLLM:

    def __init__(self):
        load_dotenv()
        self.loader = ModelLoader()
        self.llm = self.loader.load_llm()
        self.prompt = PROMPT_REGISTRY[PromptType.DOCUMENT_COMPARISON.value]
        self.parser = JsonOutputParser(pydantic_object=SummaryResponse)
        self.fixing_parser = OutputFixingParser.from_llm(self.llm, self.parser)
        self.chain = self.prompt | self.llm | self.fixing_parser
        log.info("Document comparator initialized")


    def compare_documents(self, combined_docs: str) -> pd.DataFrame:

        try:
            inputs = {
                "format_instructions": self.parser.get_format_instructions(),
                "combined_docs": combined_docs
            }

            log.info("Invoking document comparison LLM chain")
            response = self.chain.invoke(inputs)
            log.info("Chain invoked successfully", response_preview=str(response)[:200])
            return self._format_response(response)

        except Exception as e:
            log.error(f"Error comparing documents: {e}")
            raise DocumentPortalException(f"Error comparing documents: {e}", sys)

    def _format_response(self, response: list[dict]) -> pd.DataFrame: #type: ignore

        try:
            return pd.DataFrame(response)
        except Exception as e:
            log.error(f"Error formatting response: {e}")
            raise DocumentPortalException(f"Error formatting response: {e}", sys)



