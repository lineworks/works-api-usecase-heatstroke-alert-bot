from abc import ABCMeta, abstractmethod
from typing import List, Dict, Optional
from .base import BaseClass

from ..models import (
    AccessToken,
    BotClientCredential,
    BotInfo,
    InstalledApp,
)
from ..lib.aws import dynamodb

# BotInfo
class BaseBotInfoRepository(BaseClass):
    @abstractmethod
    def get_bot_info(self, bot_id: str) -> Optional[BotInfo]:
        pass


class InMemoryBotInfoRepository(BaseBotInfoRepository):
    def __init__(self):
        self.bot_infos = {}

    def get_bot_info(self, bot_id: str) -> Optional[BotInfo]:
        return self.bot_infos.get(bot_id)

    def put_bot_info(self, bot_info: BotInfo):
        self.bot_infos[bot_info.bot_id] = bot_info


class DynamoDBBotInfoRepository(BaseBotInfoRepository):
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.in_memory_repo = InMemoryBotInfoRepository()

    def get_bot_info(self, bot_id: str) -> Optional[BotInfo]:
        cache = self.in_memory_repo.get_bot_info(bot_id)
        if cache is not None:
            return cache

        _raw = dynamodb.get_item(self.table_name, {"bot_id": bot_id})
        if _raw is None:
            return None
        _item = BotInfo.parse_obj(_raw)
        self.in_memory_repo.put_bot_info(_item)
        return _item


# BotClientCredential
class BaseBotClientCredentialRepository(BaseClass):
    @abstractmethod
    def get_bot_client_credential(self, bot_id: str, domain_id: str) -> Optional[BotClientCredential]:
        pass


class InMemoryBotClientCredentialRepository(BaseBotClientCredentialRepository):
    def __init__(self):
        self.bot_client_creds = {}

    def get_bot_client_credential(self, bot_id: str, domain_id: str) -> Optional[BotClientCredential]:
        return self.bot_client_creds[bot_id].get(domain_id) if self.bot_client_creds.get(bot_id) else None

    def put_bot_client_credential(self, bot_client_cred: BotClientCredential):
        if self.bot_client_creds.get(bot_client_cred.bot_id) is None:
            self.bot_client_creds[bot_client_cred.bot_id] = {}
        self.bot_client_creds[bot_client_cred.bot_id][bot_client_cred.domain_id] = bot_client_cred


class DynamoDBBotClientCredentialRepository(BaseBotClientCredentialRepository):
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.in_memory_repo = InMemoryBotClientCredentialRepository()

    def get_bot_client_credential(self, bot_id: str, domain_id: str) -> Optional[BotClientCredential]:
        cache = self.in_memory_repo.get_bot_client_credential(bot_id, domain_id)
        if cache is not None:
            return cache

        _raw = dynamodb.get_item(self.table_name, {"bot_id": bot_id, "domain_id": domain_id})
        if _raw is None:
            return None
        _item = BotClientCredential.parse_obj(_raw)
        self.in_memory_repo.put_bot_client_credential(_item)
        return _item


# InstalledApp
class BaseInstalledAppRepository(BaseClass):
    @abstractmethod
    def get_installed_app(self, domain_id: str) -> Optional[InstalledApp]:
        pass

    @abstractmethod
    def put_installed_app(self, installed_app_obj: InstalledApp):
        pass

    @abstractmethod
    def delete_installed_app(self, domain_id: str):
        pass


class InMemoryInstalledAppRepository(BaseInstalledAppRepository):
    def __init__(self):
        self.installed_apps = {}

    def get_installed_app(self, domain_id: str) -> Optional[InstalledApp]:
        return self.installed_apps.get(domain_id)

    def put_installed_app(self, installed_app_obj: InstalledApp):
        self.installed_apps[installed_app_obj.domain_id] = installed_app_obj

    def delete_installed_app(self, domain_id: str):
            del self.installed_apps[domain_id]


class DynamoDBInstalledAppRepository(BaseInstalledAppRepository):
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.in_memory_repo = InMemoryInstalledAppRepository()

    def get_installed_app(self, domain_id: str) -> Optional[InstalledApp]:
        cache = self.in_memory_repo.get_installed_app(domain_id)
        if cache is not None:
            return cache

        _raw = dynamodb.get_item(self.table_name, {"domain_id": domain_id})
        if _raw is None:
            return None
        _item = InstalledApp.parse_obj(_raw)
        self.in_memory_repo.put_installed_app(_item)
        return _item

    def put_installed_app(self, installed_app_obj: InstalledApp):
        dynamodb.put_item(self.table_name, installed_app_obj.dict())
        self.in_memory_repo.put_installed_app(installed_app_obj)

    def delete_installed_app(self, domain_id: str):
        dynamodb.delete_item(self.table_name, {"domain_id": domain_id})


# AccessToken
class BaseAccessTokenRepository(BaseClass):
    @abstractmethod
    def get_access_token_item(self, domain_id: str) -> Optional[AccessToken]:
        pass

    @abstractmethod
    def put_access_token_item(self, access_token: AccessToken):
        pass

    @abstractmethod
    def delete_access_token_item(self, domain_id: str):
        pass


class InMemoryAccessTokenRepository(BaseAccessTokenRepository):
    def __init__(self):
        self.access_tokens = {}

    def get_access_token_item(self, domain_id: str) -> Optional[AccessToken]:
        return self.access_tokens.get(domain_id)

    def put_access_token_item(self, access_token: AccessToken):
        self.access_tokens[access_token.domain_id] = access_token

    def delete_access_token_item(self, domain_id: str):
        del self.access_tokens[domain_id]


class DynamoDBAccessTokenRepository(BaseAccessTokenRepository):
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.in_memory_repo = InMemoryAccessTokenRepository()

    def get_access_token_item(self, domain_id: str) -> Optional[AccessToken]:
        cache = self.in_memory_repo.get_access_token_item(domain_id)
        if cache is not None:
            return cache

        _raw = dynamodb.get_item(self.table_name, {"domain_id": domain_id})
        if _raw is not None:
            access_token = AccessToken.parse_obj(_raw)
            self.in_memory_repo.put_access_token_item(access_token)
            return access_token

    def put_access_token_item(self, access_token: AccessToken):
        dynamodb.put_item(self.table_name, access_token.dict())
        self.in_memory_repo.put_access_token_item(access_token)

    def delete_access_token_item(self, domain_id: str):
        dynamodb.delete_item(self.table_name, {"domain_id": domain_id})
        self.in_memory_repo.delete_access_token_item(domain_id)
