export default function Methodology() {
  return (
    <div className="methodology">
      <h1>Methodology</h1>

      <section>
        <h2>Design Philosophy</h2>
        <p><strong>Credibility over features.</strong> This system prioritizes intellectual honesty and transparency.</p>
        <ul>
          <li>Missing data is never invented</li>
          <li>Every metric includes availability status</li>
          <li>Limitations are stated explicitly</li>
        </ul>
      </section>

      <section>
        <h2>Universe Criteria</h2>
        <p>We analyze public GitHub repositories that meet ALL of:</p>
        <ul>
          <li><code>stars &gt;= 2000</code></li>
          <li><code>created_at &gt;= now() - 24 months</code> (sliding window)</li>
          <li><code>archived = false</code></li>
          <li><code>fork = false</code></li>
          <li><code>pushed_at</code> within last 90 days (for deep analysis eligibility)</li>
        </ul>
      </section>

      <section>
        <h2>Two-Stage Pipeline</h2>

        <h3>Stage A: Discovery (Weekly)</h3>
        <p>Broad, cheap scrape to find eligible repos.</p>
        <ul>
          <li>Uses GitHub Search API (~1-10 calls)</li>
          <li>Stores immutable snapshots</li>
          <li>Tracks universe changes (entered/exited/changed)</li>
        </ul>

        <h3>Stage B: Deep Analysis (Bi-weekly)</h3>
        <p>Expensive per-repo behavioral analysis.</p>
        <ul>
          <li>~60-90 API calls per repo</li>
          <li>Hard budget limit (5000 calls/run)</li>
          <li>Priority queue (newly eligible, high momentum, stale)</li>
          <li>30-day guarantee: every eligible repo analyzed at least once per month</li>
        </ul>
      </section>

      <section>
        <h2>What We Measure</h2>

        <h3>Contributor Health</h3>
        <ul>
          <li>Monthly active contributors (last 6 months)</li>
          <li>Contribution distribution</li>
          <li>Source: GitHub stats API (cached by GitHub)</li>
        </ul>

        <h3>Velocity & Trend</h3>
        <ul>
          <li>Weekly commits, PRs, issues (last 12 weeks)</li>
          <li>Trend slopes (linear regression)</li>
          <li>Source: Commit activity stats + search API</li>
        </ul>

        <h3>Responsiveness</h3>
        <ul>
          <li>Median time to first maintainer response</li>
          <li>Maintainer = OWNER, MEMBER, or COLLABORATOR</li>
          <li>Sample: 30 recent closed issues/PRs</li>
        </ul>

        <h3>Adoption Signals</h3>
        <ul>
          <li>✓ Fork-to-star ratio</li>
          <li>✗ Dependents count (requires additional API)</li>
          <li>✗ Package downloads (requires ecosystem integration)</li>
        </ul>

        <h3>Community Risk</h3>
        <ul>
          <li>Top contributor share (bus factor indicator)</li>
          <li>Active maintainers count</li>
        </ul>
      </section>

      <section>
        <h2>What We Don't Measure</h2>
        <p><strong>And why:</strong></p>
        <ul>
          <li><strong>True adoption</strong> - Requires dependency graph API with strict limits</li>
          <li><strong>npm/PyPI downloads</strong> - Requires package name detection + external APIs</li>
          <li><strong>Gini coefficient</strong> - Needs full contribution list (not partial sample)</li>
          <li><strong>Code quality</strong> - Test coverage, docs require repo cloning</li>
        </ul>
      </section>

      <section>
        <h2>Data Integrity Rules</h2>
        <ol>
          <li>Never invent missing data</li>
          <li>Never silently smooth gaps</li>
          <li>Every metric includes:
            <ul>
              <li><code>value</code></li>
              <li><code>availability</code> status</li>
              <li><code>reason</code> if missing</li>
            </ul>
          </li>
          <li>Store raw counts with derived metrics</li>
          <li>Snapshots are immutable</li>
        </ol>
      </section>

      <section>
        <h2>Limitations</h2>
        <ul>
          <li>GitHub stars are a weak proxy for quality</li>
          <li>Response time samples may not represent full history</li>
          <li>Fork-to-star ratio has selection bias</li>
          <li>Statistics API can be delayed or unavailable</li>
          <li>30-day guarantee depends on rate limit budget</li>
        </ul>
      </section>
    </div>
  )
}
