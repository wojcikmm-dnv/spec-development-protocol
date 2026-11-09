---
name: create-ui-component
description: Guidance for building accessible, testable frontend UI components. Use when creating or changing a UI component, page section, or interaction.
---

# Skill: Create UI Component

## Purpose

Produce a reusable, accessible, and testable UI component that aligns with the project's design system and conventions.

## Prerequisites

- Component purpose, props, and states are defined in the design spec.
- UI framework and design system are defined in `TECH.md`.
- The closest existing component has been read; reuse its file layout, styling approach, and test style.

## Checklist

1.  **Component Design**: Follow single responsibility. Define the props/interface first and type it in the project's language. Reuse existing design-system components before creating new ones. Provide default props.
2.  **Implementation**: Keep rendering free of side effects. Extract complex logic into the framework's reuse mechanism (a hook, composable, or service, per the stack in `TECH.md`). Use design system tokens, not inline styles. Handle all visual states (loading, empty, error, and disabled where relevant). Never inject unsanitized HTML.
3.  **Accessibility (a11y)**: Use semantic HTML. Ensure keyboard navigation and visible focus. Give every control an accessible name and every form field a label with associated error text. Add ARIA attributes only when necessary. Don't rely on color alone to convey state.
4.  **State Management**: Use local state first. Lift state only when needed. Use global state for app-wide concerns. Cancel or ignore stale async results when inputs change or the component unmounts.
5.  **Testing**: Test rendered output and user interactions, not implementation details. Cover all visual states. Use accessible queries (role, label, text). Mock external dependencies at the network or service boundary.
6.  **Documentation**: Document only non-obvious public props or behavioral
    constraints. Do not add story/task/AC comments or implementation narration.
    Export from a barrel file only when that is the project's convention.

## Quality Bar

- Renders correctly in all visual states.
- Keyboard-operable and accessible.
- Tested for each state and user interaction.
- No hardcoded styles outside the design system.
- Follows the project's framework idioms; nothing is borrowed from a different stack.
