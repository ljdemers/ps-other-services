CREATE ROLE smh_api with LOGIN NOSUPERUSER INHERIT NOCREATEDB
NOCREATEROLE NOREPLICATION password 'noan7wiu9OoF';

create database smh_service;

alter database smh_service owner to smh_api;

-- switch to new DB
\c smh_service

CREATE TABLE public.portVisits
(
  id serial NOT NULL,
  portcall_id integer,
  data_rate integer,
  visit_type character varying(50),
  imo_number character varying(7) NOT NULL,
  mmsi character varying(9),
  entered timestamp without time zone NOT NULL,
  departed timestamp without time zone,
  latitude float,
  longitude float,
  speed float,
  heading float,
  port_code character varying(25),
  ihs_port_name character varying(100),
  CONSTRAINT portVisits_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.portVisits OWNER TO smh_api;
GRANT ALL ON TABLE public.portVisits TO smh_api;

CREATE INDEX port_info
  ON public.portvisits
  USING btree
  (portcall_id, imo_number COLLATE pg_catalog."default");


CREATE TABLE public.portcalls
(
  id serial NOT NULL,
  "timestamp" timestamp with time zone,
  imo_number character varying(10),
  port_calls json NOT NULL,
  options json,
  CONSTRAINT portcalls_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.portcalls OWNER TO smh_api;
GRANT ALL ON TABLE public.portcalls TO smh_api;

CREATE INDEX "imo and timestamp"
  ON public.portcalls
  USING btree
  ("timestamp", imo_number COLLATE pg_catalog."default");


CREATE TABLE public.eez_12nm
(
    eez_code character varying(8) COLLATE pg_catalog."default" NOT NULL,
    eez_name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    latitude double precision,
    longitude double precision,
    eez_polygon geometry,
    eez_source character varying(32) COLLATE pg_catalog."default",
    country_code_id character varying(3) COLLATE pg_catalog."default" NOT NULL,
    mrg_id integer NOT NULL,
    CONSTRAINT eez_12nm_code_pkey PRIMARY KEY (mrg_id)
)
WITH (
    OIDS = FALSE
);
ALTER TABLE public.eez_12nm OWNER TO smh_api;
GRANT ALL ON TABLE public.eez_12nm TO smh_api;

CREATE TABLE public.eez_200nm
(
    eez_code character varying(8) COLLATE pg_catalog."default" NOT NULL,
    eez_name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    latitude double precision,
    longitude double precision,
    eez_polygon geometry,
    eez_source character varying(32) COLLATE pg_catalog."default",
    country_code_id character varying(3) COLLATE pg_catalog."default" NOT NULL,
    mrg_id integer NOT NULL,
    CONSTRAINT eez_200nm_code_pkey PRIMARY KEY (mrg_id)
)
WITH (
    OIDS = FALSE
);
ALTER TABLE public.eez_200nm OWNER TO smh_api;
GRANT ALL ON TABLE public.eez_200nm TO smh_api;

CREATE EXTENSION postgis;
CREATE EXTENSION pg_prewarm;

select pg_prewarm('eez_200nm')


CREATE EXTENSION pg_buffercache;
SELECT
    c.relname,
    count(*) AS buffers
FROM pg_buffercache b
INNER JOIN pg_class c
   ON b.relfilenode = pg_relation_filenode(c.oid)
    	AND b.reldatabase IN (0, (SELECT oid FROM pg_database
WHERE datname = current_database()))
GROUP BY c.relname
ORDER BY 2 DESC;


CREATE TABLE public.smh_users
(
  id serial NOT NULL,
  last_login timestamp with time zone,
  username character varying(25),
  password character varying(25),
  request_count integer DEFAULT 0,
  CONSTRAINT smh_users_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.smh_users OWNER TO smh_api;
GRANT ALL ON TABLE public.smh_users TO smh_api;


-- New cache table schema
CREATE TABLE public.smh_data
(
  id serial NOT NULL,
  "timestamp" timestamp without time zone,
  imo_number character varying(10),
  cached_days integer,
  options jsonb,
  port_visits jsonb NOT NULL,
  positions jsonb NOT NULL,
  ihs_movements jsonb NOT NULL,
  ais_gaps jsonb,
  eez_visits jsonb,
  misc_data jsonb,
  update_count integer DEFAULT 0,
  CONSTRAINT smh_data_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.smh_data OWNER TO smh_api;
GRANT ALL ON TABLE public.smh_data TO smh_api;

CREATE INDEX "imo"
  ON public.smh_data
  USING btree
  (imo_number COLLATE pg_catalog."default");


CREATE TABLE public.regions
(
    code character varying(8) COLLATE pg_catalog."default" NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    latitude double precision,
    longitude double precision,
    polygon geometry,
    source character varying(32) COLLATE pg_catalog."default",
    country_code_id character varying(3) COLLATE pg_catalog."default" NOT NULL,
    mrg_id integer NOT NULL,
    type character varying(128) COLLATE pg_catalog."default"
)
WITH (
    OIDS = FALSE
)

ALTER TABLE public.regions OWNER TO smh_api;
GRANT ALL ON TABLE public.regions TO smh_api;
