try:
    from .visualizations import main
except ImportError:  # pragma: no cover - legacy direct execution fallback
    from visualizations import main


if __name__ == "__main__":
    main()
