import argparse
from .core import Shipment, Status, transition

def main():
    parser = argparse.ArgumentParser(description="Try a shipment transition")
    parser.add_argument("current", choices=[x.value for x in Status])
    parser.add_argument("target", choices=[x.value for x in Status])
    args = parser.parse_args()
    before = Shipment("demo-001", Status(args.current))
    try:
        after = transition(before, Status(args.target))
        print(f"Allowed: {before.status.value} -> {after.status.value}")
    except ValueError as exc:
        print(str(exc))
        raise SystemExit(2) from exc

if __name__ == "__main__":
    main()
