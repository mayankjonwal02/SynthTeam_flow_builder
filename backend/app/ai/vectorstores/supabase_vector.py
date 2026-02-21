from app.ai.vectorstores.registry import register_vectorstore


@register_vectorstore("supabase")
def create_supabase_vector(**kwargs):
    from langchain_community.vectorstores import SupabaseVectorStore
    from supabase import create_client
    client = create_client(kwargs.get("url", ""), kwargs.get("api_key", ""))
    return client
