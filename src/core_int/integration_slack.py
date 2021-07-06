# Copyright (c) 2020, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import logging

from dataclasses import dataclass

from dazl import create, exercise
from dazl.model.core import ContractData

from daml_dit_if.api import \
    getIntegrationLogger, \
    IntegrationEnvironment, \
    IntegrationEvents, \
    IntegrationWebhookResponse

from daml_dit_if.main.web import json_response

from .slack_client import connect_slack_client


LOG = getIntegrationLogger()


def integration_slack_main(env: 'IntegrationEnvironment', events: 'IntegrationEvents'):

    sc = connect_slack_client(events)

    @events.ledger.contract_created('SlackIntegration.Messages:OutboundMessage')
    async def on_outbound_message(event):
        LOG.debug('Outbound message contract created: %r', event)

        channel = event.cdata['slackChannel']
        text = event.cdata['messageText']

        sc().chat_postMessage(channel=channel, text=text)

        return [exercise(event.cid, 'Archive')]

    @events.webhook.post(label='Slack Event Webhook Endpoint')
    async def on_webhook_post(request):
        body = await request.json()

        LOG.debug('Webhook event received: %r', body)

        if body['type'] == 'url_verification':
            LOG.info('URL Verification Challenge: %r', body['challenge'])

            return IntegrationWebhookResponse(
                response=json_response({'challenge': body['challenge']}))

        if body['type'] == 'event_callback' \
           and body['event']['type'] == 'message' \
           and body['event'].get('subtype') != 'bot_message':

            LOG.debug('Inbound Message: %r', body)

            return IntegrationWebhookResponse(
                commands=[create(env.tid('SlackIntegration.Messages:InboundDirectMessage'), {
                    'integrationParty': env.party,
                    'slackChannel': body['event']['channel'],
                    'slackUser': body['event']['user'],
                    'messageText': body['event']['text'],
                })])

        LOG.debug('Unhandled inbound event type: %r', body['type'])
        return IntegrationWebhookResponse()
