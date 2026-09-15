
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
from kubernetes import client, config
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
#Kubernetes connection
try:
    #running outside kubernetes
    config.load_kube_config()
    print('use local kubeconfig')
except Exception:
    #running inside kubernetes
    config.load_incluster_config()
    print('using in cluster kube config')

core_v1 = client.CoreV1Api()

#Helper function

def get_ready_status(pod) -> str:
    if not pod.status.container_statuses:
        return "Unknown"
    ready = sum(1 for container in pod.status.container_statuses if container.ready)
    total = len(pod.status.container_statuses)
    return f"{ready}/{total}"


#tool 1- get the pod details

@tool
def get_pods(namespace: str = "default") -> str:
    """
    Get all pods in the kubernetes namespace
    use this to check pod status and readiness
    """
    try:
        pods = core_v1.list_namespaced_pod(namespace=namespace)
        if not pods.items:
            return f"No pods found in {namespace} namespace"
        result = []
        for pod in pods.items():
            result.append(
                f"Pod: {pod.metadata.name}\n"
                f"status: {pod.metadata.status}"
                f"Ready: {get_ready_status(pod)}"

            )
        return "\n\n".join(result)
    except Exception as e:
        return f"error getting pod details: {str(e)}"

# TOOL 2: Get Pod Logs
def get_pod_logs(pod_name: str, namespace: str = "default", tail_lines: int = 100) -> str:
    """
    Get logs from kubernetes namespace
    use this while investigation application errors
    """
    try:
      logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace= namespace, tail_lines = tail_lines)
      if not logs:
        return "No logs available"
      return logs
    except Exception as e:
        return f"Error getting logs: {str(e)}"

# Tool 3: Describe the pod

@tool
def describe_pod(pod_name: str, namespace: str = "default") -> str:
    """
    Get detailed information about the kubernetes pod
    use this to investigate readiness, lifecycle, container and configuration problems
    """
    try:
        pod = core_v1.read_namespaced_pod(name=pod_name, namespace= namespace)
        result = []
        result.append(f"Name: {pod.metadata.name}")
        result.append(f"Namespace: {pod.metadata.namespace}")
        result.append(f"Phase: {pod.status.phase}")

        #Pod conditions

        result.append("\n Pod conditions: ")
        if pod.status.conditions:

            for condition in pod.status.conditions:

                result.append(
                    f"Type={condition.type}, "
                    f"Status={condition.status}, "
                    f"Reason={condition.reason}, "
                    f"Message={condition.message}"
                )
        # container statuses
        if pod.status.container_statuses:

            for container in pod.status.container_statuses:

                result.append(
                    f"Container={container.name}, "
                    f"Ready={container.ready}, "
                    f"RestartCount={container.restart_count}"
                )

                if container.state:

                    if container.state.waiting:

                        result.append(
                            f"Waiting Reason="
                            f"{container.state.waiting.reason}"
                        )

                    if container.state.terminated:

                        result.append(
                            f"Terminated Reason="
                            f"{container.state.terminated.reason}"
                        )       
        # ----------------------------------------------------
        # Container configuration
        # ----------------------------------------------------

        result.append("\nContainer Configuration:")

        for container in pod.spec.containers:

            result.append(
                f"Container={container.name}"
            )

            result.append(
                f"Image={container.image}"
            )

            # Readiness probe

            if container.readiness_probe:

                result.append(
                    f"Readiness Probe="
                    f"{container.readiness_probe}"
                )

            else:

                result.append(
                    "Readiness Probe=None"
                )

            # Liveness probe

            if container.liveness_probe:

                result.append(
                    f"Liveness Probe="
                    f"{container.liveness_probe}"
                )

            else:

                result.append(
                    "Liveness Probe=None"
                )

        return "\n".join(result)

    except Exception as e:
        return f"Error describing pod: {str(e)}"

#Tool 4- describe the events
@tool
def get_events(namespace: str = "default") -> str:
    """
    Get Kubernetes events from a namespace.
    Use this for troubleshooting pod failures,
    readiness probes, scheduling and other issues.
    """

    try:

        events = core_v1.list_namespaced_event(
            namespace=namespace
        )

        if not events.items:
            return f"No events found in namespace {namespace}"

        result = []

        for event in events.items[-30:]:

            result.append(
                f"Type={event.type}, "
                f"Reason={event.reason}, "
                f"Object={event.involved_object.name}, "
                f"Message={event.message}"
            )

        return "\n".join(result)

    except Exception as e:
        return f"Error getting events: {str(e)}"

tools = [get_pods, get_pod_logs, describe_pod, get_events]

#LLM

llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)

# ============================================================
# LangGraph State
# ============================================================

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Agent Node

def agent(state: AgentState):
    response = llm_with_tools.invoke(state['messages'])
    return {'messages': [response]}

#Decide next step
def should_continue(state: AgentState) -> Literal["tools", "end"]:
    last_message = state['messages'][-1]
    if hasattr(last_message, "tool_calls"):

        if last_message.tool_calls:

            return "tools"

    return "end"

# ============================================================
# Build LangGraph
# ============================================================

graph = StateGraph(AgentState)
graph.add_node('agent', agent)
graph.add_node('tools', ToolNode(tools))

graph.add_edge(START, 'agent')
graph.add_conditional_edges('agent', should_continue,{'tools': 'tools', 'end': END})
graph.add_edge('tools', 'agent')
memory = MemorySaver()
app = graph.compile(checkpointer=memory)

if __name__ == "__main__":

    print("=" * 70)
    print("KUBERNETES SRE AGENT")
    print("=" * 70)
    print("Ask me anything about your Kubernetes cluster.")
    print("Type 'exit' to quit.")
    print()

    while True:

        question = input("You: ")

        if question.lower() == "exit":
            print("Goodbye!")
            break
        config = {
         "configurable": {
               "thread_id": "123"
                          }
        }
        result = app.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=question
                    )
                ]
            },
            config=config
        )

        print("\nAgent:")
        print(result["messages"][-1].content)
        print()

