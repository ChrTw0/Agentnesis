"""
Entry Point - CLI para Fractal Cognitive Swarm System.

Inicializa el sistema y ejecuta el main graph con user query.

Usage:
    python -m src.main "Your query here"
    python -m src.main --interactive
"""

import sys
import argparse
from typing import Optional
from pathlib import Path

from src.config.settings import settings
from src.core.main_graph import compile_main_graph
from src.core.states.global_state import GlobalState
from src.utils.dev_logger import dev_logger


def create_initial_state(user_query: str) -> GlobalState:
    """
    Crea el estado inicial del sistema.

    Args:
        user_query: Query del usuario

    Returns:
        GlobalState inicializado
    """
    return {
        # Input
        "user_query": user_query,
        "domain": "",  # Genesis lo detectará

        # Agentes y spawning
        "active_agents": [],
        "dependencies": {},
        "spawn_requests": [],

        # Memoria
        "knowledge_graph": {
            "entities": {},
            "relations": []
        },
        "staging_area": {},

        # Orquestación
        "turn_history": [],
        "next_speaker": "",
        "iteration": 0,
        "max_iterations": settings.moderator.max_iterations,

        # Control de flujo
        "deadlock_detected": False,
        "needs_human_input": False,

        # Salida
        "final_output": "",
        "final_status": "incomplete"
    }


def run_system(user_query: str, verbose: bool = False) -> dict:
    """
    Ejecuta el sistema completo con una query.

    Args:
        user_query: Pregunta o tarea del usuario
        verbose: Si mostrar información detallada durante ejecución

    Returns:
        Estado final del sistema
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f" Fractal Cognitive Swarm System")
        print(f"{'='*60}")
        print(f"\n Query: {user_query}\n")
        print(f"  Configuration:")
        print(f"   - Max Agents: {settings.genesis.max_agents}")
        print(f"   - Max Iterations: {settings.moderator.max_iterations}")
        print(f"   - Model: {settings.llm.openai_model}")
        print(f"   - Developer Mode: {settings.developer.developer_mode}")
        print(f"\n{'='*60}\n")

    # Compilar main graph
    if verbose:
        print(" Compiling main graph...")

    graph = compile_main_graph(
        genesis_config=settings.genesis,
        moderator_config=settings.moderator,
        integrator_config=settings.integrator,
        worker_config=settings.worker,
        context_config=settings.context_retrieval,
        synthesizer_config=settings.synthesizer
    )

    # Crear estado inicial
    initial_state = create_initial_state(user_query)

    # Ejecutar grafo
    if verbose:
        print(" Starting execution...\n")

    try:
        final_state = graph.invoke(initial_state, config={"recursion_limit": settings.graph.recursion_limit})

        if verbose:
            print(f"\n{'='*60}")
            print(f" Execution completed")
            print(f"{'='*60}")
            print(f"\n Final Status: {final_state['final_status']}")
            print(f" Iterations: {final_state['iteration']}")
            print(f" Agents Created: {len(final_state.get('active_agents', []))}")

            if final_state.get('active_agents'):
                print(f"\n Active Agents:")
                for agent in final_state['active_agents']:
                    print(f"   - {agent.name} ({agent.role})")

            # Mostrar synthesis metadata si existe
            if final_state.get('synthesis_metadata'):
                metadata = final_state['synthesis_metadata']
                print(f"\n Synthesis Metadata:")
                print(f"   - Confidence: {metadata.get('confidence', 0):.2%}")
                print(f"   - Entities Created: {metadata.get('entities_created', 0)}")

                if metadata.get('key_decisions'):
                    print(f"\n Key Decisions:")
                    for decision in metadata['key_decisions']:
                        print(f"   - {decision}")

            print(f"\n{'='*60}")
            print(f"\n Final Output:\n")
            print(final_state['final_output'])
            print(f"\n{'='*60}\n")

        return final_state

    except Exception as e:
        print(f"\n❌ Error during execution: {e}", file=sys.stderr)
        if settings.developer.developer_mode:
            import traceback
            traceback.print_exc()
        raise

    finally:
        # Finalizar logger si está en developer mode
        if settings.developer.developer_mode:
            dev_logger.finalize_run()
            if verbose:
                print(f"\n Developer logs saved to: {dev_logger.run_dir}")


def interactive_mode():
    """
    Modo interactivo: permite múltiples queries en sesión.
    """
    print(f"\n{'='*60}")
    print(f" Fractal Cognitive Swarm - Interactive Mode")
    print(f"{'='*60}\n")
    print("Type 'exit' or 'quit' to end session.")
    print("Type 'help' for commands.\n")

    while True:
        try:
            user_input = input("🔹 Query: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break

            if user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("  exit/quit - Exit interactive mode")
                print("  help      - Show this help")
                print("  config    - Show current configuration")
                print("  Any other text will be processed as a query\n")
                continue

            if user_input.lower() == 'config':
                print(f"\nCurrent Configuration:")
                print(f"  - Max Agents: {settings.genesis.max_agents}")
                print(f"  - Max Iterations: {settings.moderator.max_iterations}")
                print(f"  - Model: {settings.llm.openai_model}")
                print(f"  - Temperature: {settings.llm.llm_temperature}")
                print(f"  - Developer Mode: {settings.developer.developer_mode}\n")
                continue

            # Ejecutar query
            run_system(user_input, verbose=True)

        except KeyboardInterrupt:
            print("\n\n Interrupted by user. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n", file=sys.stderr)
            if settings.developer.developer_mode:
                import traceback
                traceback.print_exc()


def main():
    """
    Main entry point - parsea args y ejecuta sistema.
    """
    parser = argparse.ArgumentParser(
        description="Fractal Cognitive Swarm System - Multi-Agent Problem Solver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single query
  python -m src.main "Design a REST API for user management"

  # Interactive mode
  python -m src.main --interactive

  # Quiet mode (only final output)
  python -m src.main "Analyze GDPR compliance requirements" --quiet
        """
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="User query to process"
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Start interactive mode"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode - only show final output"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose mode - show detailed execution info (default)"
    )

    args = parser.parse_args()

    # Validar input
    if args.interactive:
        interactive_mode()
    elif args.query:
        verbose = not args.quiet
        final_state = run_system(args.query, verbose=verbose)

        # Si está en quiet mode, solo imprimir output
        if args.quiet:
            print(final_state['final_output'])

        # Exit code basado en status
        if final_state['final_status'] == 'success':
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
