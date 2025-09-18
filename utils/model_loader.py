import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from exceptions.custom_exception import DocumentPortalException
from logger import GLOBAL_LOGGER as log
from utils.config_loader import load_config



class ApiKeyManager:
    REQUIRED_KEYS = [
        "GOOGLE_API_KEY",
        "GROQ_API_KEY",
    ]
    
    # Optional keys that might be used in some deployments
    OPTIONAL_KEYS = [
        "HF_TOKEN",
        "LANGCHAIN_API_KEY",
    ]
    
    def __init__(self):
        self.api_key = {}

        # Method 1: Try to load from JSON environment variable (for local development)
        raw = os.getenv('API_KEY')
        if raw:
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("API_KEY must be a valid JSON object")
                self.api_key = parsed
                log.info("API_KEYS parsed from JSON successfully")
            except Exception as e:
                log.warning("Failed to parse API_KEYS as JSON", error=str(e))    
        
        # Method 2: Load individual environment variables (for production/AWS Secrets Manager)
        all_keys = self.REQUIRED_KEYS + self.OPTIONAL_KEYS
        for key in all_keys:
            if not self.api_key.get(key):
                env_val = os.getenv(key)
                if env_val:
                    self.api_key[key] = env_val
                    log.info(f"API_KEY {key} loaded from environment variables")

        # Check for missing required keys
        missing = [key for key in self.REQUIRED_KEYS if not self.api_key.get(key)]
        if missing:
            log.warning(f"Missing required API_KEYS", missing=missing)
            raise DocumentPortalException("Missing required API_KEYS", missing)

        # Log loaded keys (with masked values for security)
        loaded_keys = {k: v[:6]+"..." if len(v) > 6 else "***" for k, v in self.api_key.items()}
        log.info("API_KEYS loaded successfully", keys=loaded_keys)
                
        

    def get(self, key: str):
        """Get an API key. Raises KeyError if not found."""
        val = self.api_key.get(key)
        if not val:
            log.warning(f"API_KEY {key} not found", key=key)
            raise KeyError(f"API_KEY {key} not found")
        return val
    
    def get_optional(self, key: str, default: str = None):
        """Get an optional API key. Returns default if not found."""
        return self.api_key.get(key, default)
    
    def has_key(self, key: str) -> bool:
        """Check if an API key is available."""
        return key in self.api_key and bool(self.api_key[key])

class ModelLoader:

    def __init__(self):

        if os.getenv("ENV","local").lower() != "production":
            load_dotenv()
            log.info("Running in local mode, .env loaded")

        else:
            log.info("Running in production mode")

        self.api_key_manager = ApiKeyManager()
        self.config = load_config()
        log.info("YAML config loaded", config_keys=list(self.config.keys()))

    def load_llm(self):

        llm_block = self.config.get("llm",{})

        provider_key = os.getenv("LLM_PROVIDER","google")

        if provider_key not in llm_block:
            log.error("LLM provider not found in config", provider=provider_key)
            raise ValueError(f"LLM provider '{provider_key}' not found in config")

        llm_config = llm_block.get(provider_key,{})
        provider = llm_config.get("provider")
        model_name = llm_config.get("model_name")
        temperature = llm_config.get("temperature",0.2)
        max_tokens = llm_config.get("max_tokens",2048)

        log.info("Loading LLM", provider=provider, model_name=model_name, temperature=temperature, max_tokens=max_tokens)

        if provider == "google":
            return ChatGoogleGenerativeAI(
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.api_key_manager.get("GOOGLE_API_KEY")
            )
        elif provider == "groq":
            return ChatGroq(
                model_name=model_name,
                temperature=temperature,
                api_key=self.api_key_manager.get("GROQ_API_KEY")

            )

        else:
            log.error("Invalid LLM provider", provider=provider)
            raise ValueError(f"Invalid LLM provider '{provider}'")


    def load_embedding_model(self):

        try:
            model_name = self.config["embedding_model"]["model_name"]
            log.info("Loading embedding model", model=model_name)
            return GoogleGenerativeAIEmbeddings(
                model=model_name,
                google_api_key=self.api_key_manager.get("GOOGLE_API_KEY")
            )
        except Exception as e:
            log.error("Failed to load embedding model", error=str(e))
            raise ValueError(f"Failed to load embedding model: {str(e)}")

if __name__ == "__main__":
    loader = ModelLoader()

    # Test Embedding
    embeddings = loader.load_embedding_model()
    print(f"Embedding Model Loaded: {embeddings}")
    result = embeddings.embed_query("Hello, how are you?")
    print(f"Embedding Result: {result}")

    # Test LLM
    llm = loader.load_llm()
    print(f"LLM Loaded: {llm}")
    result = llm.invoke("Hello, how are you?")
    print(f"LLM Result: {result.content}")

        
        