from slack import WebClient

from daml_dit_if.api import \
    getIntegrationLogger, \
    IntegrationEvents


LOG = getIntegrationLogger()


def connect_slack_client(events: 'IntegrationEvents'):
    sc = None

    @events.ledger.contract_created('SlackIntegration.Configuration:Configuration')
    async def on_configuration_create(event):
        nonlocal sc

        LOG.info('Configuration contract created: %r', event)

        slackApiToken = event.cdata['slackApiToken']

        sc = WebClient(slackApiToken, run_async=True)

    @events.ledger.contract_archived('SlackIntegration.Configuration:Configuration')
    async def on_configuration_archive(event):
        nonlocal sc

        LOG.info('Configuration contract archived: %r', event)

        sc = None

    def get_slack_client():
        nonlocal sc

        if sc == None:
            raise Exception('No configuration contract. No action taken.')

        return sc

    return get_slack_client
