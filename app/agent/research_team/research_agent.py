from langchain_core.prompts import ChatPromptTemplate
from .research_state import CompanyResearchState
from app.utils.prompt_utils import load_prompt
from app.tool.tavily_search import tavily_search
from app.core.llm_factory import LLMFactory, ModelRole
import json

# 1. Product Worker

def research_product(state: CompanyResearchState):
    company = state["company_name"]

    llm = LLMFactory.create(ModelRole.WORKER)
    
    # 1. 强制搜索
    search_results = tavily_search.invoke({
        "query": f"{company} product overview core features target users official site"
    })

    # 2. 读取prompt
    prompt_text = load_prompt("research_product.md")
    
    # 3. 将真实的搜索结果给LLM
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
         company: {company}

         Here are real web search results:
         {search_results}

         you MUST answer only based on the search results above.
         Do NOT use prior knowledge.
         Do NOT invent facts.
         If the evidence is insufficient, explicitly say what is missing.
         """)
    ])

    chain = prompt | llm
    response = chain.invoke({
        "company": company,
        "search_results": json.dumps(search_results, ensure_ascii=False, indent=2)
    })

    # 4. 用真实source
    real_source = [
        {"company": company, "dimension": "Product", "url": item.get("url", "")}
        for item in search_results[:5]
    ]
    
    # TODO: get real url from tool
    # mock_source = [{"company": company, "dimension": "Product", "url": "https://example.com/product"}]   

    # return the updated states var
    return {
        "product_info": response.content,
        "reference_sources": real_source
    }

# 2. Market Worker

def research_market(state: CompanyResearchState):
    company = state["company_name"]
    llm = LLMFactory.create(ModelRole.WORKER)

    search_results = tavily_search.invoke({
        "query": f"{company} user reviews reputation pain points competitors moat"
    })
    
    # 1. Read system prompt
    prompt_text = load_prompt("research_market.md")
    
    # 2. Integrate prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
         company: {company}

         Here are real web search results:
         {search_results}

         You MUST answer only based on the search results above.
         Do NOT use prior knowledge.
         Do NOT invent facts.
         If the evidence is insufficient, explicitly say what is missing.
         """)
    ]) 

    # 3. Chaining prompt with llm
    chain = prompt | llm

    # 4. Execute chain
    response = chain.invoke({
        "company": company, 
        "search_results": json.dumps(search_results, ensure_ascii=False, indent=2)
    })
    
    real_source = [
        {"company": company, "dimension": "Market", "url": item.get("url", "")}
        for item in search_results[:5]
    ]
    
    return {
        "market_info": response.content,
        "reference_sources": real_source
    }


# 3. Business Worker

def research_business(state: CompanyResearchState):
    company = state["company_name"]
    llm = LLMFactory.create(ModelRole.WORKER)

    search_results = tavily_search.invoke({
        "query": f"{company} pricing revenue funding investors growth business model"
    })

    # 1. Read system prompt
    prompt_text = load_prompt("research_business.md")
    
    # 2. Integrate prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
         company: {company}
         
         Here are real web search results:
         {search_results}
         
         You MUST answer only based on the search results above.
         Do NOT use prior knowledge.
         Do NOT invent facts.
         If the evidence is insufficient, explicitly say what is missing.
         """)
    ])

    # 3. Chaining prompt with llm
    chain = prompt | llm

    # 4. Execute chain
    response = chain.invoke({
        "company": company,
        "search_results": json.dumps(search_results, ensure_ascii=False, indent=2)
    })

    real_source = [
        {"company": company, "dimension": "Business", "url": item.get("url", "")}
        for item in search_results[:5]
    ]
    
    return {
        "business_info": response.content,
        "reference_sources": real_source
    }

# 4. Synthesizer

def synthesize_profile(state: CompanyResearchState):
    company = state["company_name"]

    llm = LLMFactory.create(ModelRole.COMPACTOR)

    # 1. Read system prompt
    prompt_text = load_prompt("research_synthesize.md")
    
    # 2. Integrate prompt template (Synthesizer requires multiple inputs)
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
         product research report:
         {product_info}

         ---
         market research report:
         {market_info}

         ---
         business research report:
         {business_info}
         """)
    ]) 

    # 3. Chaining
    chain = prompt | llm

    # 4. Execute chain with all context
    response = chain.invoke({
        "company": company,
        "product_info": state.get('product_info', 'no info'),
        "market_info": state.get('market_info', 'no info'),
        "business_info": state.get('business_info', 'no info')
    })
    
    return {
        "company_profile": response.content
    }
