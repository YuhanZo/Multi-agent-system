from langchain_core.prompts import ChatPromptTemplate
from .research_state import CompanyResearchState
from app.utils.prompt_utils import load_prompt
from app.tool.tavily_search import tavily_search
from app.core.llm_factory import LLMFactory, ModelRole

# 1. Product Worker

def research_product(state: CompanyResearchState):
    company = state["company_name"]

    search_tool = [tavily_search]
    llm = LLMFactory.create(ModelRole.WORKER,"qwen")
    llm_with_tools = llm.bind_tools(search_tool)
    
    # 1. Read system prompt
    prompt_text = load_prompt("research_product.md")
    
    # 2. Integrate prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", "please do a research on company: {company}")
    ]) 

    # 3. Chaining prompt with llm
    chain = prompt | llm

    # 4. Execute chain
    response = chain.invoke({"company": company})
    
    # TODO: get real url from tool
    mock_source = [{"company": company, "dimension": "Product", "url": "https://example.com/product"}]   

    # return the updated states var
    return {
        "product_info": response.content,
        "reference_sources": mock_source
    }

# 2. Market Worker

def research_market(state: CompanyResearchState):
    company = state["company_name"]

    search_tool = [tavily_search]
    llm = LLMFactory.create(ModelRole.WORKER,"qwen")
    llm_with_tools = llm.bind_tools(search_tool)
    
    # 1. Read system prompt
    prompt_text = load_prompt("research_market.md")
    
    # 2. Integrate prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", "please do a research on company: {company}")
    ]) 

    # 3. Chaining prompt with llm
    chain = prompt | llm

    # 4. Execute chain
    response = chain.invoke({"company": company})
    
    mock_source = [{"company": company, "dimension": "Market", "url": "https://example.com/reviews"}]
    
    return {
        "market_info": response.content,
        "reference_sources": mock_source
    }


# 3. Business Worker

def research_business(state: CompanyResearchState):
    company = state["company_name"]

    search_tool = [tavily_search]
    llm = LLMFactory.create(ModelRole.WORKER,"qwen")
    llm_with_tools = llm.bind_tools(search_tool)    

    # 1. Read system prompt
    prompt_text = load_prompt("research_business.md")
    
    # 2. Integrate prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", "please do a research on company: {company}")
    ]) 

    # 3. Chaining prompt with llm
    chain = prompt | llm

    # 4. Execute chain
    response = chain.invoke({"company": company})
    
    mock_source = [{"company": company, "dimension": "Business", "url": "https://example.com/funding"}]
    
    return {
        "business_info": response.content,
        "reference_sources": mock_source
    }

# 4. Synthesizer

def synthesize_profile(state: CompanyResearchState):
    company = state["company_name"]

    search_tool = [tavily_search]
    llm = LLMFactory.create(ModelRole.COMPACTOR,"qwen")
    llm_with_tools = llm.bind_tools(search_tool)

    # 1. Read system prompt
    prompt_text = load_prompt("research_synthesize.md")
    
    # 2. Integrate prompt template (Synthesizer requires multiple inputs)
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
        "product research report":\n{product_info}
        \n---\n
        market research report:\n{market_info}
        \n---\n
        business research report:\n{business_info}
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
