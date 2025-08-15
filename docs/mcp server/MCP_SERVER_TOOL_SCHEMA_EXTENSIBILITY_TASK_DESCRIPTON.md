now the plan is to make the mcp server generic for this we have created the refined mcp server tools but each of these tools will have different context for their usage , when the underlying documentation pipeline + mcp server will be used for different contexts. Like previously the mcp server tools were very relevant only for the work item usecase.

Now that we have a feasible plan in place with enhanced filter builder (need to be absolutely sure of the accuracy of this as this is very cruucial for extensibility of mcp tools). I am thinking the next step is to change the tool schemas , since the tool schema is essentially the place where the details of the tools are mentioned, and the LLM will use this schema to identify how to effectively used the mcp tools to achieve efficient documentation retrieval for the specific usecase.
There is therefore a need to make the tool schemas abstract , and the individual concretion will depend on the use case of the mcp server . the use case can maybe be better specified in the client side of the mcp server. And depdneing on the usecase of the mcp server the appropriate tool schemas will be registered to the mcp server.

Now if the above is successfully implemented then i will have the freedom to use the same underlying mcp tools for a wide variety of usecases will it not.
Also by making the tool schema closer to the usecase i get the freedom to put more information specific to the usecase in the toolschemas right ? This will further improve extensibility as by simply modifying the tool schema string i will also be able to inform the LLM of how to use the outputs of a tool call more efficiently for that particular usecase.

Now with current codebase state , there are legacy tools and univeral tools. Internally the legacy tools are implemented with specific assumptions about the work item context, while the universal tools are designed to be more flexible and adaptable to different contexts. And the legacy tools use the universal tools.
So it can be considered that the legacy tools are very specific implementations built on top of the more general universal tools.

This layered architecture allows for greater flexibility and adaptability in the MCP server's toolset, enabling it to cater to a wider range of use cases while maintaining a solid foundation.

Now the need is to make the code cleaner , currently the work item documentation specific tools are registered as legacy tools. And also there is no mechanism to extarct the particular use case for the mcp server in order to dynamically register only those tools which are specific to the use case.

Help me come up with a plan to achieve this. FFor this do websearches to gather as much information wherever needed.
After doing the necessary research come up with an accurate plan for achieving this.
Also analyse what all changes will need to be made to the codebase in order to implement this plan.
Output this plan in a markdown file.

FFinally make sure to double check your work.
