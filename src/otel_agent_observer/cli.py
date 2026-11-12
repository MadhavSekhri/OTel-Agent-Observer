"""Run a simulated local observation."""
import sys
from .observer import AgentObserver, jsonl_sink


def main(argv=None):
    observer = AgentObserver(sink=jsonl_sink(sys.stdout))
    with observer.span("example.llm.request", {
        "model": "simulated",
        "api_key": "not-a-real-key",
        "tokens": 20,
    }):
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
