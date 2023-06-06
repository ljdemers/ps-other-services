import pytest
from freezegun import freeze_time
from screening_api.screenings.enums import Severity


class TestScreeningShipInfoViewOptions:
    @pytest.fixture
    def screening(self, factory):
        account_id = 654321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/reports/ship_info'.format(
            screening_id)

    def test_allowed_methods(self, test_client, screening):
        env, resp = test_client.options(
            self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


class TestScreeningShipInspectionsViewOptions:
    @pytest.fixture
    def screening(self, factory):
        account_id = 654321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/reports/ship_inspections'.format(
            screening_id)

    def test_allowed_methods(self, test_client, screening):
        env, resp = test_client.options(
            self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestScreeningShipInfoReportViewGet:
    @pytest.fixture
    def screening(self, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/reports/ship_info'.format(
            screening_id)

    def test_unauthenticated(self, test_client, screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client, screening):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, screening):
        report = factory.create_screening_report(screening=screening)

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert resp.json == {
            "data": report.ship_info,
        }


@pytest.mark.usefixtures('authenticated')
class TestScreeningShipInspectionsReportViewGet:
    @pytest.fixture
    def screening(self, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/reports/ship_inspections'.format(
            screening_id)

    def test_unauthenticated(self, test_client, screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client, screening):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, screening):
        report = factory.create_screening_report(screening=screening)

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert resp.json == {
            "data": report.ship_inspections,
        }


class TestScreeningShipSanctionsViewOptions:
    @pytest.fixture
    def screening(self, factory):
        account_id = 654321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/reports/ship_sanctions'.format(
            screening_id)

    def test_allowed_methods(self, test_client, screening):
        env, resp = test_client.options(
            self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'GET', 'HEAD'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestScreeningShipSanctionsReportViewGet:
    @pytest.fixture
    def screening(self, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/reports/ship_sanctions'.format(
            screening_id)

    def test_unauthenticated(self, test_client, screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client, screening):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, screening):
        report = factory.create_screening_report(screening=screening)

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert resp.json == {
            "data": report.ship_sanction,
        }


@pytest.mark.usefixtures('authenticated')
class TestScreeningCountrySanctionsReportViewGet:
    @pytest.fixture
    def screening(self, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/reports/country_sanctions'.format(
            screening_id)

    def test_unauthenticated(self, test_client, screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client, screening):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, screening):
        report = factory.create_screening_report(screening=screening)

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert resp.json == {
            "data": {
                'ship_flag': report.ship_flag,
                'ship_registered_owner': report.ship_registered_owner,
                'ship_operator': report.ship_operator,
                'ship_beneficial_owner': report.ship_beneficial_owner,
                'ship_manager': report.ship_manager,
                'ship_technical_manager': report.ship_technical_manager,
            },
        }


@pytest.mark.usefixtures('authenticated')
class TestScreeningShipMovementsReportViewGet:
    @pytest.fixture
    def screening(self, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/reports/ship_movements'.format(
            screening_id)

    def test_unauthenticated(self, test_client, screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client, screening):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, screening):
        report = factory.create_screening_report(screening=screening)

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert resp.json == {
            "data": report.port_visits,
        }


@pytest.mark.usefixtures('authenticated')
class TestScreeningCompanySanctionsReportViewGet:
    @pytest.fixture
    def screening(self, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/reports/company_sanctions'.format(
            screening_id)

    def test_unauthenticated(self, test_client, screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client, screening):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, screening):
        report = factory.create_screening_report(screening=screening)

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert resp.json == {
            "data": {
                'ship_registered_owner_company':
                    report.ship_registered_owner_company,
                'ship_operator_company':
                    report.ship_operator_company,
                'ship_beneficial_owner_company':
                    report.ship_beneficial_owner_company,
                'ship_manager_company':
                    report.ship_manager_company,
                'ship_technical_manager_company':
                    report.ship_technical_manager_company,
                'ship_company_associates':
                    report.ship_company_associates,
            },
        }


@pytest.mark.usefixtures('authenticated')
class TestScreeningPdfReportViewGet:
    @pytest.fixture
    def screening(self, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id):
        return '/v1/screenings/{0}/report'.format(
            screening_id)

    def test_unauthenticated(self, test_client, screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client, screening):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, screening):
        report = factory.create_screening_report(screening=screening)

        env, resp = test_client.get(
            self.get_uri(screening.id), as_tuple=True)

        assert report is not None
        assert resp.status_code == 200

        assert resp is not None


@pytest.mark.usefixtures('authenticated')
class TestScreeningHistoryPdfReportViewGet:
    @pytest.fixture
    def screening(self, factory):
        account_id = 54321
        imo_id = 654321
        ship_1 = factory.create_ship(imo_id=imo_id, country_id='PL')
        return factory.create_screening(
            account_id=account_id, ship=ship_1, severity=Severity.UNKNOWN)

    def get_uri(self, screening_id, history_id=123):
        return '/v1/screenings/{0}/history/{1}/report'.format(
            screening_id, history_id)

    def test_unauthenticated(self, test_client, screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.get_uri(screening.id), as_tuple=True)

        assert resp.status_code == 401

    def test_screening_not_found(self, test_client, screening):
        screening_id = 0
        env, resp = test_client.get(self.get_uri(screening_id), as_tuple=True)

        assert resp.status_code == 404

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, screening):
        report = factory.create_screenings_history(screening=screening)

        env, resp = test_client.get(self.get_uri(
            screening.id, report.id), as_tuple=True)

        assert report is not None
        assert resp.status_code == 200

        assert resp is not None
