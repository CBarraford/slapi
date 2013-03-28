import string
import os
import sys
import SoftLayer.API

from util.config import config
from util.helpers import format_object

def get_account_service(object_id=None):
    return _get_service('SoftLayer_Account', object_id)

def get_hardware_server_service(object_id=None):
    return _get_service('SoftLayer_Hardware_Server', object_id)

def _get_service(name, object_id=None):
    api_user = config['softlayer']['api_user']
    api_key = config['softlayer']['api_key']
    return SoftLayer.API.Client(name, object_id, api_user, api_key)

class softlayer_property(object):
    def __init__(self, method):
        self.method = method
        self.__name__ = method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, obj, cls=None):
        result = self.method(obj)
        #obj.__dict__[self.__name__] = result
        return result

    def __set__(self, obj, value):
        raise AttributeError("This property is read-only")

    def __delete__(self,inst):
        raise AttributeError("This property is read-only")

def softlayer_property_format(property_name_format=None, property_display=True):
    """factory function for softlayer_property__format_decorator"""
    def softlayer_property_format_decorator(func):
        @softlayer_property
        def wrapped_f(*args):
            return func(*args)
        # set property_format
        wrapped_f.property_name_format = property_name_format
        wrapped_f.property_display = property_display
        return wrapped_f
    return softlayer_property_format_decorator

def softlayer_object_property(object_type, property_name_format=None, property_display=True):
    """factory function for softlayer_object_property_decorator"""
    def softlayer_object_property_decorator(func):
        @softlayer_property
        def wrapped_f(*args):
            obj = func(*args)
            if obj:
                return object_type(obj)
            else:
                return None
        wrapped_f.property_name_format = property_name_format
        wrapped_f.property_display = property_display
        return wrapped_f
    return softlayer_object_property_decorator

class BaseSoftLayerObject(object):
    """Base SoftLayer Object"""

    def __init__(self, obj):
        self._data = obj

    def __getitem__(self, k):
        if k in self.data:
            return self.data[k]
        else:
            return None

    @property
    def data(self):
        return self._data

    def format(self, mask=None, only_locals=False, color=True):
        obj = self._format(mask, only_locals)
        return format_object(obj, color=color)

    def _format(self, mask, only_locals):
        obj = {}
        #TODO: sort local first?
        for key, method in self.__class__.__dict__.iteritems():
            if isinstance(method, softlayer_property):
                property_display = getattr(method, 'property_display', True)
                if not property_display:
                    continue

                property_name = getattr(method, 'property_name_format', key)
                if property_name is None or property_name == key:
                    property_name = string.capwords(' '.join(key.split('_')))

                property_value = method.__get__(self, key)
                if property_value:
                    if isinstance(property_value, BaseSoftLayerObject):
                        if not only_locals:
                            obj[property_name] = property_value._format(mask, only_locals)
                    else:
                        obj[property_name] = property_value
        return obj

class SoftLayerLocation(BaseSoftLayerObject):
    """SoftLayer_Location"""

    def __init__(self, obj):
        super(SoftLayerLocation, self).__init__(obj)

    @softlayer_property_format(property_display=False)
    def id(self):
        return self.data['id']

    @softlayer_property_format("Short Name")
    def name(self):
        return self.data['name']

    @softlayer_property_format("Name")
    def pretty_name(self):
        return self.data['longName']

class SoftLayerTransactionGroup(BaseSoftLayerObject):
    """SoftLayer_Provisioning_Version1_Transaction_Group"""

    def __init__(self, obj):
        super(SoftLayerTransactionGroup, self).__init__(obj)

    @softlayer_property
    def name(self):
        return self.data['name']

    @softlayer_property
    def average_time(self):
        return self.data['averageTimeToComplete']

class SoftLayerTransactionStatus(BaseSoftLayerObject):
    """SoftLayer_Provisioning_Version1_Transaction_Status"""

    def __init__(self, obj):
        super(SoftLayerTransactionStatus, self).__init__(obj)

    @softlayer_property_format(property_display=False)
    def name(self):
        return self.data['name']

    @softlayer_property_format("Name")
    def pretty_name(self):
        return self.data['friendlyName']

class SoftLayerTransaction(BaseSoftLayerObject):
    """SoftLayer_Provisioning_Version1_Transaction"""

    def __init__(self, obj):
        super(SoftLayerTransaction, self).__init__(obj)

    @softlayer_property
    def create_date(self):
        return self.data['createDate']

    @softlayer_property
    def modify_date(self):
        return self.data['modifyDate']

    @softlayer_object_property(SoftLayerTransactionStatus)
    def status(self):
        return self['transactionStatus']

    @softlayer_object_property(SoftLayerTransactionGroup)
    def group(self):
        return self['transactionGroup']

class SoftLayerHardwareServer(BaseSoftLayerObject):

    def __init__(self, obj):
        super(SoftLayerHardwareServer, self).__init__(obj)

    @softlayer_property_format("Id")
    def id(self):
        return self.data['id']

    @softlayer_property_format("AccountId")
    def account_id(self):
        return self.data['accountId']

    @softlayer_property
    def domain(self):
        return self.data['domain']

    @softlayer_property
    def hostname(self):
        return self.data['hostname']

    @softlayer_property_format("FQDN")
    def fqdn(self):
        return self.data['fullyQualifiedDomainName']

    @softlayer_property_format("Public IP")
    def public_ip_address(self):
        return self.data['primaryIpAddress']

    @softlayer_property_format("Private IP")
    def private_ip_address(self):
        return self.data['primaryBackendIpAddress']

    @softlayer_property_format("Management IP")
    def management_ip_address(self):
        return self.data['networkManagementIpAddress']

    @softlayer_property
    def serial_number(self):
        return self.data['serialNumber']

    @softlayer_object_property(SoftLayerLocation)
    def datacenter(self):
        return self['datacenter']

    @softlayer_object_property(SoftLayerTransaction, property_name_format="Last Transaction")
    def last_transaction(self):
        return self['lastTransaction']
