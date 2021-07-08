# Copyright (c) 2020, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import datetime

from dataclasses import dataclass

from aiohttp import ClientSession

from dazl import create, exercise
from dazl.model.core import ContractData

from daml_dit_if.api import \
    empty_success_response, \
    json_response, \
    getIntegrationLogger, \
    IntegrationEnvironment, \
    IntegrationEvents, \
    IntegrationWebhookResponse

from .slack_client import connect_slack_client


LOG = getIntegrationLogger()


def current_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def integration_slack_main(env: 'IntegrationEnvironment', events: 'IntegrationEvents'):

    sc = connect_slack_client(events)

    @events.ledger.contract_created('SlackIntegration.Messages:OutboundMessage')
    async def on_outbound_message(event):
        LOG.debug('Outbound message contract created: %r', event)

        channel = event.cdata['slackChannel']
        text = event.cdata['messageText']

        sc().chat_postMessage(channel=channel, text=text)

        return [exercise(event.cid, 'Archive')]

    @events.ledger.contract_created('SlackIntegration.Commands:CommandInvocationResponse')
    async def on_command_response(event):
        LOG.debug('Command invocation response requested: %r', event)

        async with ClientSession() as session:
            async with session.post(event.cdata['responseUrl'], json={
                    'text': event.cdata['responseText']
            }) as resp:

                if resp.status == 200:
                    return [exercise(event.cid, 'Archive')]
                else:
                    return [exercise(event.cid, 'ResponseFailed', {
                        'receivedAt': current_time(),
                        'httpStatusCode': resp.status,
                        'httpResponseBody': await resp.text()
                    })]

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
                    'receivedAt': current_time(),
                    'slackChannel': body['event']['channel'],
                    'slackUser': body['event']['user'],
                    'messageText': body['event']['text'],
                })])

        LOG.warn('Unhandled inbound event type from Slack: %r', body['type'])

        return IntegrationWebhookResponse()

    async def on_command_invocation(request):
        LOG.debug('Inbound Command Invocation: %r', request)

        body = await request.post()

        LOG.debug('Command body: %r', body)

        return IntegrationWebhookResponse(
            response=empty_success_response(),
            commands=[create(env.tid('SlackIntegration.Commands:CommandInvocation'), {
                'integrationParty': env.party,
                'receivedAt': current_time(),
                'command': body.getone('command', None),
                'commandText': body.getone('text', None),
                'responseUrl': body.getone('response_url', None),
                'slackUser': body.getone('user_id', None),
                'slackTeam': body.getone('team_id', None),
                'slackChannel': body.getone('channel_id', None),
                'slackApiAppId': body.getone('api_app_id', None)
            })])

    @events.webhook.post(label='Slack Webhook Endpoint - Events and Commands')
    async def on_http_post(request):
        LOG.debug('Inbound HTTP request: %r', request)

        content_type = request.content_type

        LOG.debug('Inbound request content type: %r', content_type)

        # Slack sends command invocations using a different content
        # type than the usual JSON payload used for webhook posts.

        if content_type == "application/x-www-form-urlencoded":
            return await on_command_invocation(request)
        else:
            return await on_webhook_post(request)
