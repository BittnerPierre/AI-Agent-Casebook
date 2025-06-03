---

**Advanced Retrieval for AI with Chroma - Introduction**

**Retrieval Augmented Generation (RAG)**

RAG, or Retrieval Augmented Generation, retrieves relevant documents to provide context to an LLM (Large Language Model). This approach significantly improves the ability of an LLM to answer queries and perform tasks. Many teams utilize simple retrieval techniques based on semantic similarity or embeddings. However, in this course, you'll learn more sophisticated techniques that will allow you to achieve far better results.

A typical workflow in RAG involves embedding a query and then finding the most similar documents—those with similar embeddings—to establish context. A notable pitfall of this approach is that it often retrieves documents that discuss similar topics but do not contain the actual answer. To address this, you can rewrite the initial user query. This technique, known as query expansion, allows you to draw in more directly related documents.

**Key Techniques**

Two key techniques related to query expansion are:

1. Expanding the original query into multiple queries by rewording or rewriting it in various ways.
2. Hypothesizing what the answer might look like to locate documents in the collection that resemble an answer rather than generally discussing the query's topics.

**Course Overview**

I'm delighted to introduce your instructor for this course, Anton Troynikov. Anton is a leading innovator in advancing the state-of-the-art in retrieval for AI applications. He is the co-founder of Chroma, which offers one of the most popular open-source vector databases. If you've participated in our LangChain short courses taught by Harrison Chase, you likely have used Chroma.

Anton will work with you throughout this course, sharing insights about what succeeds and what doesn’t in RAG deployments. We will begin with a quick review of RAG applications and explore some retrieval pitfalls where simple vector searches might fall short. Following this, you will learn several methods to enhance retrieval outcomes.

**Methods to Improve Retrieval**

As mentioned by Andrew, the initial methods involve using an LLM to refine the query itself. Another approach involves re-ranking query results using a cross encoder, which evaluates sentence pairs and assigns a relevancy score. Furthermore, you will discover how to modify query embeddings based on user feedback to produce more relevant results.

**Cutting Edge Techniques**

Significant innovations are happening in RAG presently. Therefore, the final lesson will cover cutting-edge techniques not yet mainstream but emerging in research. We anticipate these methods will soon gain broader adoption.

**Acknowledgments**

We extend our gratitude to the individuals contributing to this course.

- From the Chroma team: Jeff Huber, Hammad Bashir, Liquan Pei, Ben Eggers, and the Chroma open-source developer community.
- From the Deep Learning team: Geoff Ladwig and Esmael Gargari.

**Conclusion**

The first lesson provides an overview of RAG. We hope you’ll start there immediately after this introduction. With these techniques, smaller teams can now build effective systems that were not viable before. Upon completing this course, you might accomplish something truly remarkable with an approach once considered a RAG tag.