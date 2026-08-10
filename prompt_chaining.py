# Store the review produced for each changed file so the results can be
# combined into a single context for the later review stages.
file_review =[]
for file in changed_files:
    # Ask Claude to inspect each file independently for correctness, edge
    # cases, and violations of the project's style expectations.
    review = claude(
        prompt = f"Review {file} for: corectness, edge cases, style violations",
        context=read_file(file)
    )
    # Keep each file-level review available for the integration pass.
    file_reviews.append(review)

# Look across all individual reviews to identify issues that affect multiple
# files or arise from interactions between them.
integration_issues = claude(
    prompt="Given these per-file reviews, idenfiy cross-cutting concerns.",
    context="\n".join(file_reviews)
)

# Produce the final, severity-ranked summary from the cross-cutting findings.
final_report = claude(
    prompt="Generate a PR review summary, rank issues by severity",
    context=integration_issues
)
