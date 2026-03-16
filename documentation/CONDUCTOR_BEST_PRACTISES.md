
# Gemini CLI Conductor: Best Practices for Existing Projects

To get the best out of the **Gemini CLI Conductor extension**—especially when modifying an existing (or "brownfield") project—you need to lean heavily into its core philosophy: **"Measure twice, code once."**

Unlike standard AI chat interfaces that lose context over time, Conductor uses **Context-Driven Development (CDD)**. It shifts the context out of transient chat logs and into persistent Markdown files stored directly in your repository.

Here is the step-by-step workflow and the best practices for safely and effectively modifying an existing project with Conductor.

---

## 1. The Setup Phase: Establish the "Brain" of Your Project

When you introduce Conductor to an existing codebase, it doesn't just guess how your app works. You must run `/conductor:setup`. The AI will scan your repository, analyze your commit history, and ask clarifying questions to generate a `conductor/` directory.

### Best Practices:
*   **Audit the Generated Files:** Conductor will generate `product.md` (goals/users), `tech-stack.md` (languages/frameworks), and `workflow.md` (testing/PR rules). **Do not blindly accept them.** Read through them and manually add any "unwritten rules" your project has (e.g., *"We use Tailwind for all styling, never inline CSS,"* or *"Always favor React Server Components over Client Components"*).
*   **Define Your Testing Strategy:** In your `workflow.md`, explicitly define your testing requirements. For example, mandate that the AI must write failing tests before implementing a feature (Test-Driven Development).
*   **Customize the Style Guides:** Conductor will try to generate style guides based on your existing code. If your existing code is messy or has legacy patterns you are trying to move away from, update the style guide to enforce the *new* standards you want the AI to use moving forward.

## 2. Planning the Modification: Start a "Track"

When you want to add a feature, fix a bug, or refactor existing code, run `/conductor:newTrack`. A track is a logical unit of work. Conductor will ask you what you want to achieve and generate a `spec.md` (the requirements) and a `plan.md` (a step-by-step to-do list).

### Best Practices:
*   **Keep Tracks Granular:** Don't ask Conductor to "Refactor the entire backend." Instead, create a track to "Refactor the Auth middleware," then another to "Migrate the User database schema."
*   **Review the `plan.md` Carefully:** This is where you catch AI hallucinations *before* they ruin your codebase. Review the plan to ensure it plans to interact with your existing components correctly, rather than hallucinating new libraries or duplicate files.
*   **Force Architectural Alignment:** If the plan suggests a route you don't like, tell the CLI to revise the plan before you let it write a single line of code.

## 3. Execution: Implementing the Changes

Once you are happy with the `plan.md`, run `/conductor:implement`. The AI will now act as an autonomous agent, checking off tasks, writing code, creating tests, and making localized Git commits for each completed step.

### Best Practices:
*   **Respect the Checkpoints:** Conductor doesn't just blast through the whole plan. It inserts manual validation checkpoints at the end of phases. Actually spin up your local server and test the app at these pauses. If a component breaks, report the exact error back to the CLI so it can fix the issue before moving to the next phase.
*   **Use the Smart Revert:** If a specific phase completely messes up your existing code, do not panic. Use `/conductor:revert`. Unlike a standard `git reset`, Conductor's revert is context-aware and will roll back specific logical units of work (tracks, phases, or tasks) by intelligently analyzing the Git history.

## 4. Post-Modification: Wrapping Up

After the track is successfully implemented and tested, Conductor will ask if you want to archive or delete the track plan.

### Best Practices:
*   **Always Archive, Never Delete:** Archiving the track moves it to an archive folder, preserving the history of *how* and *why* a feature was designed. This is incredibly valuable context for the AI when you need to modify that same feature months down the line.
*   **Sync the Global Context:** Run `/conductor:sync`. If your new feature introduced a new global pattern, database table, or dependency, this command updates your root `product.md` and `tech-stack.md` so that the AI remembers this new architecture for the *next* track.

---

## 💡 Summary Tip: Treat Markdown as Code

To get the absolute best out of Conductor, treat the `.md` files in your `conductor/` folder with the same respect you treat your source code. If you manually refactor a part of your existing app without the AI, take 60 seconds to update the `tech-stack.md` or `product.md` file. 

By keeping the documentation perfectly in sync with reality, you ensure the AI always acts as a senior engineer who knows your codebase inside and out, rather than a junior developer flying blind.