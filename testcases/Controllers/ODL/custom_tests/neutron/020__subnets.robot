*** Settings ***
Documentation     Checking Subnets created in OpenStack are pushed to OpenDaylight
Suite Setup       Create Session    OSSession    http://${OPENSTACK}:9696    headers=${X-AUTH}
Suite Teardown    Delete All Sessions
Library           Collections
Library           RequestsLibrary
Variables         ../../../variables/Variables.py

*** Variables ***
${ODLREST}        /controller/nb/v2/neutron/subnets
${OSREST}         /v2.0/subnets
${data}           {"subnet":{"network_id":"${NETID}","ip_version":4,"cidr":"172.16.64.0/24","allocation_pools":[{"start":"172.16.64.20","end":"172.16.64.120"}]}}

*** Test Cases ***
Check OpenStack Subnets
    [Documentation]    Checking OpenStack Neutron for known subnets
    [Tags]    Subnets Neutron OpenStack
    Log    ${X-AUTH}
    ${resp}    get request    OSSession    ${OSREST}
    Should be Equal As Strings    ${resp.status_code}    200
    ${OSResult}    To Json    ${resp.content}
    Log    ${OSResult}

Check OpenDaylight subnets
    [Documentation]    Checking OpenDaylight Neutron API for known subnets
    [Tags]    Subnets Neutron OpenDaylight
    Create Session    ODLSession    http://${ODL_SYSTEM_IP}:${PORT}    headers=${HEADERS}    auth=${AUTH}
    ${resp}    get request    ODLSession    ${ODLREST}
    Should be Equal As Strings    ${resp.status_code}    200
    ${ODLResult}    To Json    ${resp.content}
    Log    ${ODLResult}

Create New subnet
    [Documentation]    Create new subnet in OpenStack
    [Tags]    Create Subnet OpenStack Neutron
    Log    ${data}
    ${resp}    post request    OSSession    ${OSREST}    data=${data}
    Should be Equal As Strings    ${resp.status_code}    201
    ${result}    To JSON    ${resp.content}
    ${result}    Get From Dictionary    ${result}    subnet
    ${SUBNETID}    Get From Dictionary    ${result}    id
    Log    ${result}
    Log    ${SUBNETID}
    Set Global Variable    ${SUBNETID}
    sleep    2

Check New subnet
    [Documentation]    Check new subnet created in OpenDaylight
    [Tags]    Check    subnet OpenDaylight
    ${resp}    get request    ODLSession    ${ODLREST}/${SUBNETID}
    Should be Equal As Strings    ${resp.status_code}    200
