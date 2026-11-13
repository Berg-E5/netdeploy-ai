from app.catalog import build_plan, compatibility, CATALOG
from app.executor import validate_host
import pytest

GOOD = {"OS_ID":"debian", "ARCH":"x86_64", "UID":"0", "FREE_KB":"3000000", "DOCKER":"yes", "COMPOSE":"yes", "UDP_51820":"free", "SYSTEMD":"yes", "XUI_PRESENT":"no", "SS_AVAILABLE":"yes", "GIT_AVAILABLE":"yes", "SUI_PRESENT":"no", "DOCKGE_PRESENT":"no", "DOCKGE_TCP_5001":"free"}

# 自建 Web 应用 (物流报价 / 音乐解锁) 走 nginx 反代, 需要域名和空闲的 80/443。
WEB_FACTS = dict(GOOD, TCP_80="free", TCP_443="free", QUOTE_PRESENT="no", MUSIC_PRESENT="no")

# 需要用户填写域名才能出方案的项目 —— 遍历目录时按项目补上最小可用参数。
PROJECT_OPTIONS = {
    "logistics-quote": {"domain": "quote.example.com"},
    "music-unlock": {"domain": "music.example.com"},
}


def _options(project):
    return PROJECT_OPTIONS.get(project)


def _facts_for(project):
    return WEB_FACTS if project in PROJECT_OPTIONS else GOOD


def test_catalog_has_known_projects():
    # 目录是可扩展的: 上游自带的必须都在, 自建的两个也必须在。
    upstream = {"3x-ui", "3x-ui-https", "sing-box", "hysteria2", "wg-easy", "s-ui",
                "s-ui-https", "dockge", "dockge-access", "3x-ui-http", "hiddify"}
    assert upstream <= set(CATALOG)
    assert {"logistics-quote", "music-unlock"} <= set(CATALOG)


def test_supported_recipes_executable():
    got = set()
    for p in CATALOG:
        if CATALOG[p].get('internal'):
            continue
        if build_plan(p, _facts_for(p), _options(p))['executable']:
            got.add(p)
    assert got == {'3x-ui', 'wg-easy', 'sing-box', 's-ui', 'dockge',
                   'logistics-quote', 'music-unlock'}


def test_xui_pinned_install_plan_requires_compatibility():
    from app.three_x_ui import VERSION, INSTALLER_SHA256
    facts=dict(GOOD, OS_ID='ubuntu', OS_VERSION='26.10', DOCKER='no', COMPOSE='no')
    plan=build_plan('3x-ui',facts,{'panel_port':25443})
    assert plan['executable'] is True
    assert plan['options']=={'panel_port':25443}
    assert len(plan['steps'])==5
    scripts='\n'.join(s['script'] for s in plan['steps'])
    assert VERSION in scripts and INSTALLER_SHA256 in scripts
    assert 'XUI_NONINTERACTIVE=1' in scripts
    assert 'XUI_SSL_MODE=none' in scripts
    assert 'XUI_PANEL_PORT=25443' in scripts
    assert 'XUI_ENABLE_FAIL2BAN=false' in scripts
    assert 'bind_local="y"' in scripts
    assert 'systemctl stop x-ui' in scripts
    assert '127.0.0.1:25443' in scripts
    assert 'docker' not in scripts.lower()


@pytest.mark.parametrize('change', [
    {'OS_ID':'alpine'}, {'ARCH':'mips'}, {'UID':'1000'}, {'SYSTEMD':'no'},
    {'XUI_PRESENT':'yes'}, {'XUI_PRESENT':'unknown'}, {'SS_AVAILABLE':'no'},
    {'FREE_KB':'100000'}
])
def test_xui_safely_blocked_if_host_does_not_match(change):
    plan=build_plan('3x-ui',dict(GOOD,**change))
    assert not plan['executable'] and plan['steps']==[]


@pytest.mark.parametrize('bad_port', [0,22,1023,65536,'24443',True,None,24443.5,'$(id)'])
def test_xui_port_rejects_invalid_input(bad_port):
    with pytest.raises(ValueError):
        build_plan('3x-ui', GOOD, {'panel_port':bad_port})


def test_xui_rejects_unknown_options_and_other_projects_reject_custom_options():
    with pytest.raises(ValueError):
        build_plan('3x-ui', GOOD, {'panel_port':24443,'inject':'echo hi'})
    with pytest.raises(ValueError):
        build_plan('wg-easy', GOOD, {'panel_port':24443})


def test_incompatible_distro_blocks_package_install():
    plan = build_plan('sing-box', dict(GOOD, OS_ID='alpine'))
    assert not plan['executable']
    assert not plan['steps']


def test_missing_docker_blocks_wg_easy():
    plan = build_plan('wg-easy', dict(GOOD, DOCKER='no'))
    assert not plan['eligible'] and not plan['executable']


def test_non_root_blocks_install():
    plan=build_plan('sing-box',dict(GOOD, UID='1000'))
    assert not plan['executable']


def test_failed_guard_has_no_remote_steps():
    for p in CATALOG:
        if CATALOG[p].get('internal'): continue  # Internal HTTPS upgrades need a validated live managed installation.
        x=build_plan(p, dict(_facts_for(p), ARCH='mips'), _options(p))
        assert not x['executable'] and not x['steps']


@pytest.mark.parametrize('hostname,username,port',[
    ('-evil.com','root',22),('example.com;id','root',22),('example..com','root',22),
    ('safe.com','root;id',22),('safe.com','root',65536),('safe.com','root',0),
    ('10.0.0.1 | bash','root',22)
])
def test_rejects_host_shell_injection(hostname,username,port):
    with pytest.raises(ValueError):validate_host(hostname,username,port)


def test_accepts_normal_hostnames():
    validate_host('example.com','root',22)
    validate_host('203.0.113.11','ubuntu',2200)


def test_shell_scripts_are_fixed_and_contain_no_user_input():
    p=build_plan('wg-easy',GOOD)
    assert p['steps']
    assert all('NETDEPLOY' in s['script'] or 'docker' in s['script'] for s in p['steps'])
    assert '127.0.0.1:51821' in p['steps'][1]['script']


# ---------------------------------------------------------------- 自建 Web 应用


@pytest.mark.parametrize('project', ['logistics-quote', 'music-unlock'])
def test_web_app_requires_domain(project):
    with pytest.raises(ValueError):
        build_plan(project, WEB_FACTS)


@pytest.mark.parametrize('project', ['logistics-quote', 'music-unlock'])
def test_web_app_rejects_bad_domain(project):
    for bad in ('http://a.com', 'a.com/x', 'a.com:80', 'nodot', 'a..com', 'a.com;id',
                '-bad.example.com', 'bad-.example.com', 'a' * 70 + '.com',
                '.a.com', 'a.com.'):
        with pytest.raises(ValueError):
            build_plan(project, WEB_FACTS, {'domain': bad})


@pytest.mark.parametrize('project', ['logistics-quote', 'music-unlock'])
def test_web_app_plan_pins_commit_and_verifies_sha256(project):
    from app import web_apps
    plan = build_plan(project, WEB_FACTS, _options(project))
    assert plan['eligible'] and plan['executable']
    scripts = '\n'.join(s['script'] for s in plan['steps'])
    commit = (web_apps.LOGISTICS_QUOTE_COMMIT if project == 'logistics-quote'
              else web_apps.MUSIC_UNLOCK_COMMIT)
    sha = (web_apps.LOGISTICS_QUOTE_INSTALL_SHA256 if project == 'logistics-quote'
           else web_apps.MUSIC_UNLOCK_INSTALL_SHA256)
    # 固定 commit, 不追分支
    assert commit in scripts
    assert 'refs/heads' not in scripts and 'main.tar.gz' not in scripts
    # 校验不过就中止
    assert sha in scripts and 'sha256sum -c -' in scripts


@pytest.mark.parametrize('project', ['logistics-quote', 'music-unlock'])
def test_web_app_blocks_when_port_or_site_conflicts(project):
    for facts in (dict(WEB_FACTS, TCP_80='busy'), dict(WEB_FACTS, TCP_443='busy')):
        plan = build_plan(project, facts, _options(project))
        assert not plan['eligible'] and not plan['executable']
        assert plan['steps'] == []
        assert plan['issues']


def test_quote_app_blocks_when_already_installed():
    plan = build_plan('logistics-quote', dict(WEB_FACTS, QUOTE_PRESENT='yes'), _options('logistics-quote'))
    assert not plan['executable'] and plan['steps'] == []
    assert any('已存在' in i for i in plan['issues'])


def test_music_app_blocks_when_already_installed():
    plan = build_plan('music-unlock', dict(WEB_FACTS, MUSIC_PRESENT='yes'), _options('music-unlock'))
    assert not plan['executable'] and plan['steps'] == []


@pytest.mark.parametrize('project', ['logistics-quote', 'music-unlock'])
def test_web_app_acceptance_checks_nginx_is_running(project):
    plan = build_plan(project, WEB_FACTS, _options(project))
    acceptance = '\n'.join(s['script'] for s in plan['steps'] if '验收' in s['label'])
    assert 'systemctl is-active --quiet nginx' in acceptance
    # 只看 nginx -t 不够 —— "装了但没启动" 时配置语法照样通过
    assert 'nginx -t' in acceptance


def test_quote_app_acceptance_reads_port_from_file():
    plan = build_plan('logistics-quote', WEB_FACTS, _options('logistics-quote'))
    acceptance = '\n'.join(s['script'] for s in plan['steps'] if '验收' in s['label'])
    assert 'data/port' in acceptance


def test_web_app_install_pins_source_repo():
    from app import web_apps
    assert web_apps.LOGISTICS_QUOTE_REPO == 'Berg-E5/logistics-quote'
    assert web_apps.MUSIC_UNLOCK_REPO == 'Berg-E5/music-unlock'
    assert len(web_apps.LOGISTICS_QUOTE_COMMIT) == 40
    assert len(web_apps.MUSIC_UNLOCK_COMMIT) == 40
    assert len(web_apps.LOGISTICS_QUOTE_INSTALL_SHA256) == 64
    assert len(web_apps.MUSIC_UNLOCK_INSTALL_SHA256) == 64
