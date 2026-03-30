import { Link } from 'react-router-dom'
import { ConfigEditor } from '@/components/ConfigEditor'
import { CopyButton } from '@/components/CopyButton'

const BASE_CONFIG_YAML = `extensions:
  opamp:
    server:
      http:
        endpoint: http://localhost:8000/v1/opamp
    agent_description:
      non_identifying_attributes:
        service.name: my-collector
        host.name: \${env:HOSTNAME}
        service.instance.id: \${env:POD_NAME}
        deployment.environment: production
        host.ip: \${env:HOST_IP}

service:
  extensions: [opamp]`

export function GettingStartedPage() {
  const serverEndpoint = `${window.location.origin}/v1/opamp`

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-semibold text-foreground mb-8">Getting Started</h1>

      {/* Section 1: What is OpAMP? */}
      <section className="mb-10">
        <h2 className="text-xl font-semibold text-foreground mb-3">What is OpAMP?</h2>
        <p className="text-foreground-secondary leading-relaxed">
          OpAMP (Open Agent Management Protocol) is a CNCF standard for remotely managing
          OpenTelemetry Collectors. This server implements the OpAMP specification, allowing
          collectors to register themselves, report health and config, and receive config
          updates from this dashboard.
        </p>
      </section>

      {/* Section 2: Connect a Collector */}
      <section>
        <h2 className="text-xl font-semibold text-foreground mb-4">Connect a Collector</h2>

        <ol className="space-y-6 list-none">
          {/* Step 1 */}
          <li className="flex gap-4">
            <span className="flex-none flex h-7 w-7 items-center justify-center rounded-full bg-otel-blue text-sm font-semibold text-white shadow-[0_0_8px_rgba(66,92,199,0.4)]">
              1
            </span>
            <div className="flex-1">
              <p className="font-semibold text-foreground mb-1">
                Install the OpenTelemetry Contrib Collector
              </p>
              <p className="text-foreground-muted text-sm">
                Download the{' '}
                <a
                  href="https://github.com/open-telemetry/opentelemetry-collector-releases/releases"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-otel-blue hover:text-blue-300 underline transition-colors"
                >
                  otelcol-contrib release
                </a>{' '}
                for your platform.
              </p>
            </div>
          </li>

          {/* Step 2 */}
          <li className="flex gap-4">
            <span className="flex-none flex h-7 w-7 items-center justify-center rounded-full bg-otel-blue text-sm font-semibold text-white shadow-[0_0_8px_rgba(66,92,199,0.4)]">
              2
            </span>
            <div className="flex-1">
              <p className="font-semibold text-foreground mb-1">
                Add the OpAMP extension to your collector config
              </p>
              <p className="text-foreground-muted text-sm mb-3">
                Add the following to your collector's{' '}
                <code className="bg-otel-blue-subtle px-1.5 py-0.5 rounded text-foreground-secondary text-xs font-mono">
                  config.yaml
                </code>
                :
              </p>
              <div className="relative">
                <ConfigEditor value={BASE_CONFIG_YAML} readOnly={true} />
                <div className="absolute top-2 right-2">
                  <CopyButton text={BASE_CONFIG_YAML} label="Copy Config" />
                </div>
              </div>
            </div>
          </li>

          {/* Step 3 */}
          <li className="flex gap-4">
            <span className="flex-none flex h-7 w-7 items-center justify-center rounded-full bg-otel-blue text-sm font-semibold text-white shadow-[0_0_8px_rgba(66,92,199,0.4)]">
              3
            </span>
            <div className="flex-1">
              <p className="font-semibold text-foreground mb-1">
                Start (or restart) your collector
              </p>
              <p className="text-foreground-muted text-sm">
                Once the collector starts with this config, it will appear in the{' '}
                <Link to="/collectors" className="text-otel-blue hover:text-blue-300 underline transition-colors">
                  Collectors
                </Link>{' '}
                list within a few seconds.
              </p>
            </div>
          </li>
        </ol>

        {/* Server URL display */}
        <div className="mt-8 rounded-lg border border-border-accent bg-card p-4">
          <p className="text-xs font-medium text-foreground-subtle uppercase tracking-wider mb-2">
            Your server's OpAMP endpoint
          </p>
          <div className="flex items-center gap-3">
            <code className="font-mono text-otel-amber text-sm break-all flex-1">
              {serverEndpoint}
            </code>
            <CopyButton text={serverEndpoint} />
          </div>
        </div>
      </section>
    </div>
  )
}
