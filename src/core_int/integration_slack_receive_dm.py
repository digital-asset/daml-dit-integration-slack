# Copyright (c) 2020, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import logging

from dataclasses import dataclass

from dazl import create
from dazl.model.core import ContractData
from slack import WebClient

from daml_dit_api import \
    IntegrationEnvironment, IntegrationEvents, IntegrationWebhookResponse

from daml_dit_if.main.web import json_response


LOG = logging.getLogger('integration')


def integration_slack_receive_dm_main(
        env: 'IntegrationEnvironment',
        events: 'IntegrationEvents'):

    @events.webhook.post(label='Slack Event Webhook Endpoint')
    async def on_webhook_post(request):
        body = await request.json()

        if body['type'] == 'url_verification':
            LOG.info('URL Verification Challenge: %r', body['challenge'])

            return IntegrationWebhookResponse(
                response=json_response({'challenge': body['challenge']}))

        if body['type'] == 'event_callback' and body['event']['type'] == 'message' \
           and body['event'].get('subtype') != 'bot_message':

            LOG.debug('Inbound Message: %r', body)

            return IntegrationWebhookResponse(
                commands=[create('SlackIntegration.InboundDirectMessage.InboundDirectMessage', {
                    'integrationParty': env.party,
                    'slackChannel': body['event']['channel'],
                    'slackUser': body['event']['user'],
                    'messageText': body['event']['text'],
                })])

        LOG.debug('Unhandled inbound event type: %r', body['type'])
        return IntegrationWebhookResponse()
