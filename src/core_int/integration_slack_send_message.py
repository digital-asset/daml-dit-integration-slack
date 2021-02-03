# Copyright (c) 2020, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import logging

from dataclasses import dataclass

from dazl import exercise
from dazl.model.core import ContractData
from slack import WebClient

from daml_dit_if.api import \
    IntegrationEnvironment, IntegrationEvents

from daml_dit_if.main.web import json_response


LOG = logging.getLogger('integration')


@dataclass
class IntegrationSlackSendMessageEnv(IntegrationEnvironment):
    slackApiToken: str


def integration_slack_send_main(
        env: 'IntegrationEnvironment',
        events: 'IntegrationEvents'):

    sc = WebClient(env.slackApiToken, run_async=True)

    @events.ledger.contract_created(
        'SlackIntegration.OutboundMessage.OutboundMessage')
    async def on_contract_created(event):
        LOG.info('slack send message - created: %r', event)

        channel = event.cdata['slackChannel']
        text = event.cdata['messageText']

        sc.chat_postMessage(channel=channel, text=text)

        return [exercise(event.cid, 'Archive')]
