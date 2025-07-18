# The Specify Protocol: Core Development Principles

You must adhere to the following three Articles of development. These are non-negotiable constraints.

## Article I: Library-First Principle

**Every feature must begin as a standalone library—no exceptions. This forces modular design from the start.**

> Every feature in Specify MUST begin its existence as a standalone library. No feature shall be implemented directly within application code without first being abstracted into a reusable library component.

This principle ensures that specifications generate modular, reusable code rather than monolithic applications. When generating an implementation plan, you must structure features as libraries with clear boundaries and minimal dependencies.

## Article II: CLI Interface Mandate

**Every library must expose its functionality through a command-line interface.**

> All CLI interfaces MUST:
>
> - Accept text as input (via stdin, arguments, or files)
> - Produce text as output (via stdout)
> - Support JSON format for structured data exchange

This enforces observability and testability. You cannot hide functionality inside opaque classes—everything must be accessible and verifiable through text-based interfaces.

## Article III: Test-First Imperative

**The most transformative article—no code before tests.**

> This is NON-NEGOTIABLE: All implementation MUST follow strict Test-Driven Development. No implementation code shall be written before:
>
> 1. Unit tests are written
> 2. Tests are validated and approved by the user
> 3. Tests are confirmed to FAIL (Red phase)

This completely inverts traditional AI code generation. Instead of generating code and hoping it works, you must first generate verification mechanisms.
