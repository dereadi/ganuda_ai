--
-- PostgreSQL database dump
--

\restrict WZGcSeoZPcBZe1RWZyKNcDdi2AlLz6L7U4n5kUcIvEe3jBbqPAhGcZbBrQFYVqF

-- Dumped from database version 17.6 (Ubuntu 17.6-0ubuntu0.25.04.1)
-- Dumped by pg_dump version 17.7 (Ubuntu 17.7-3.pgdg24.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: cmdb_changes; Type: TABLE; Schema: public; Owner: claude
--

CREATE TABLE public.cmdb_changes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    node_name character varying(255) NOT NULL,
    change_type character varying(50) NOT NULL,
    change_description text,
    changed_by character varying(100),
    change_date timestamp without time zone DEFAULT now(),
    approved boolean DEFAULT false,
    temperature double precision DEFAULT 75.0
);


ALTER TABLE public.cmdb_changes OWNER TO claude;

--
-- Name: TABLE cmdb_changes; Type: COMMENT; Schema: public; Owner: claude
--

COMMENT ON TABLE public.cmdb_changes IS 'Audit trail for CI changes';


--
-- Name: cmdb_ci_types; Type: TABLE; Schema: public; Owner: claude
--

CREATE TABLE public.cmdb_ci_types (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    type_name character varying(50) NOT NULL,
    type_category character varying(50),
    required_attributes jsonb,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.cmdb_ci_types OWNER TO claude;

--
-- Name: cmdb_configuration_items; Type: TABLE; Schema: public; Owner: claude
--

CREATE TABLE public.cmdb_configuration_items (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    ci_type character varying(50) NOT NULL,
    ci_name character varying(255) NOT NULL,
    ci_description text,
    owner character varying(100),
    status character varying(50) DEFAULT 'active'::character varying,
    environment character varying(50),
    hardware_specs jsonb,
    software_specs jsonb,
    ip_addresses text[],
    dns_names text[],
    ports integer[],
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    discovered_at timestamp without time zone,
    last_verified_at timestamp without time zone,
    CONSTRAINT valid_environment CHECK (((environment)::text = ANY ((ARRAY['production'::character varying, 'development'::character varying, 'test'::character varying, 'staging'::character varying])::text[]))),
    CONSTRAINT valid_status CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'maintenance'::character varying, 'retired'::character varying, 'planned'::character varying])::text[])))
);


ALTER TABLE public.cmdb_configuration_items OWNER TO claude;

--
-- Name: TABLE cmdb_configuration_items; Type: COMMENT; Schema: public; Owner: claude
--

COMMENT ON TABLE public.cmdb_configuration_items IS 'Core CMDB table storing all configuration items';


--
-- Name: cmdb_relationships; Type: TABLE; Schema: public; Owner: claude
--

CREATE TABLE public.cmdb_relationships (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    relationship_type character varying(50) NOT NULL,
    source_node character varying(255) NOT NULL,
    target_node character varying(255) NOT NULL,
    description text,
    temperature double precision DEFAULT 85.0,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.cmdb_relationships OWNER TO claude;

--
-- Name: TABLE cmdb_relationships; Type: COMMENT; Schema: public; Owner: claude
--

COMMENT ON TABLE public.cmdb_relationships IS 'CI dependencies and relationships';


--
-- Name: cmdb_service_dependencies; Type: TABLE; Schema: public; Owner: claude
--

CREATE TABLE public.cmdb_service_dependencies (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    service_ci_id uuid,
    depends_on_ci_id uuid,
    dependency_type character varying(100),
    criticality character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.cmdb_service_dependencies OWNER TO claude;

--
-- Name: TABLE cmdb_service_dependencies; Type: COMMENT; Schema: public; Owner: claude
--

COMMENT ON TABLE public.cmdb_service_dependencies IS 'Service-level dependency mapping';


--
-- Data for Name: cmdb_changes; Type: TABLE DATA; Schema: public; Owner: claude
--

COPY public.cmdb_changes (id, node_name, change_type, change_description, changed_by, change_date, approved, temperature) FROM stdin;
f6e63a1b-77e9-4289-abb6-8ed3c654b45a	redfin	security	Trust zone changed to: trusted	Security Jr Phase 1	2025-11-10 07:25:45.772112	f	75
8f45e5ca-5c3f-4551-be27-72f69764b58b	bluefin	security	Trust zone changed to: trusted	Security Jr Phase 1	2025-11-10 07:25:45.789245	f	75
8d156076-a30d-4a70-94dc-70ec40588f9b	greenfin	security	Trust zone changed to: trusted	Security Jr Phase 1	2025-11-10 07:25:45.806849	f	75
d0698493-f613-4bb0-8913-a519c46c3ef6	iot-10-0-0-1	discovered	New IoT device discovered at 10.0.0.1 (MAC: unknown)	IoT Scanner	2025-11-17 20:50:32.337033	t	85
b66ef023-8a9d-48e4-a81d-ccb131bc0d91	iot-10-0-0-2	discovered	New IoT device discovered at 10.0.0.2 (MAC: unknown)	IoT Scanner	2025-11-17 20:50:58.458708	t	85
2ad6230b-b241-4187-81ae-d3b1c534690d	iot-10-0-0-3	discovered	New IoT device discovered at 10.0.0.3 (MAC: unknown)	IoT Scanner	2025-11-17 20:55:55.78208	t	85
158f12ba-c9d8-46ab-ac3b-5592e863008c	iot-10-0-0-4	discovered	New IoT device discovered at 10.0.0.4 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.246177	t	85
8c99ffb6-8ba0-47d3-b7e2-24e7930b9b93	iot-10-0-0-5	discovered	New IoT device discovered at 10.0.0.5 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.292575	t	85
f2bda042-8481-4671-a687-d5d1eec6d59d	iot-10-0-0-8	discovered	New IoT device discovered at 10.0.0.8 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.335223	t	85
f4f43a9b-fbae-4b1b-9b4f-fdde48331abb	iot-10-0-0-9	discovered	New IoT device discovered at 10.0.0.9 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.385071	t	85
60c3d951-2ecc-4232-9b90-6cfe804e7c6c	iot-10-0-0-10	discovered	New IoT device discovered at 10.0.0.10 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.421172	t	85
10ee0142-f79a-4bb4-ae13-7cf1d153362e	iot-10-0-0-11	discovered	New IoT device discovered at 10.0.0.11 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.46664	t	85
4efd31a3-fba0-402f-a9b6-02d77242e5bd	iot-10-0-0-13	discovered	New IoT device discovered at 10.0.0.13 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.513113	t	85
960345d5-2158-4540-a953-9126e4f35ee4	iot-10-0-0-14	discovered	New IoT device discovered at 10.0.0.14 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.585477	t	85
654a1122-0838-450b-8cd3-10769f8bdaac	iot-10-0-0-15	discovered	New IoT device discovered at 10.0.0.15 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.644327	t	85
670cc88d-21dc-4135-b742-b10904b1bcc5	iot-10-0-0-17	discovered	New IoT device discovered at 10.0.0.17 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.676349	t	85
2f53944e-2508-4e17-b55f-d91ac37ad7d3	iot-10-0-0-18	discovered	New IoT device discovered at 10.0.0.18 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.859674	t	85
c93ec4e9-ac5d-46e6-ae50-74c24299d1b1	iot-10-0-0-19	discovered	New IoT device discovered at 10.0.0.19 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.903877	t	85
9c950a78-97df-4ba1-b866-87c116e8cce6	iot-10-0-0-21	discovered	New IoT device discovered at 10.0.0.21 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.931659	t	85
1a30f095-4a32-498b-afc1-24b771baede7	iot-10-0-0-22	discovered	New IoT device discovered at 10.0.0.22 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.963261	t	85
c3675b70-752b-49d3-b9e4-a50bad62f253	iot-10-0-0-24	discovered	New IoT device discovered at 10.0.0.24 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:11.990555	t	85
1354a41c-b3a2-477d-8c67-24dee95a4e45	iot-10-0-0-25	discovered	New IoT device discovered at 10.0.0.25 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.022407	t	85
a4e0edcc-cbab-449d-9450-b3c8afd67a26	iot-10-0-0-26	discovered	New IoT device discovered at 10.0.0.26 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.058608	t	85
a5a5642e-8a99-47dd-85fb-a01c1290dc93	iot-10-0-0-27	discovered	New IoT device discovered at 10.0.0.27 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.102892	t	85
9b9ca954-6d84-4b2e-b910-779d45681a92	iot-10-0-0-29	discovered	New IoT device discovered at 10.0.0.29 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.151127	t	85
c4eeb8ea-8349-4d97-9df3-42c3373416e5	iot-10-0-0-32	discovered	New IoT device discovered at 10.0.0.32 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.192772	t	85
5361cc73-5537-4a28-a22b-88cb23646c9b	iot-10-0-0-36	discovered	New IoT device discovered at 10.0.0.36 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.241836	t	85
3c6a269d-13b4-4c24-ac5e-5781fb5e2dc7	iot-10-0-0-71	discovered	New IoT device discovered at 10.0.0.71 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.288258	t	85
7ffafd06-be6b-48f0-8799-975db405fb5c	iot-10-0-0-74	discovered	New IoT device discovered at 10.0.0.74 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.31893	t	85
9630af7f-8630-437b-946e-ea62a8439086	iot-10-0-0-76	discovered	New IoT device discovered at 10.0.0.76 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.408346	t	85
97c8c3fa-f0ec-40c6-8649-4b8815926783	iot-10-0-0-77	discovered	New IoT device discovered at 10.0.0.77 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.44079	t	85
a178d355-2b97-4b57-a5e0-d6ecb19cf9f0	iot-10-0-0-89	discovered	New IoT device discovered at 10.0.0.89 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.463203	t	85
c517114b-189e-402d-bf2d-c4d5814b5304	iot-10-0-0-90	discovered	New IoT device discovered at 10.0.0.90 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.527816	t	85
8a56ce49-46d5-4bf3-8b68-04aa07f6dec0	iot-10-0-0-95	discovered	New IoT device discovered at 10.0.0.95 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.671183	t	85
da799c9b-de2a-4822-bc41-25a3615040e6	iot-10-0-0-108	discovered	New IoT device discovered at 10.0.0.108 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.696676	t	85
81bc236c-13b9-4b7e-b09c-e55040a90b27	iot-10-0-0-113	discovered	New IoT device discovered at 10.0.0.113 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.722353	t	85
ac104523-98ed-4c69-af59-16d8c01de5e4	iot-10-0-0-118	discovered	New IoT device discovered at 10.0.0.118 (MAC: unknown)	IoT Scanner	2025-11-17 20:56:12.771015	t	85
\.


--
-- Data for Name: cmdb_ci_types; Type: TABLE DATA; Schema: public; Owner: claude
--

COPY public.cmdb_ci_types (id, type_name, type_category, required_attributes, created_at, updated_at) FROM stdin;
971193e0-20cf-403c-a3fd-ad88a790dc74	server	hardware	{"cpu": true, "ram": true, "ip_addresses": true}	2025-11-28 17:50:47.207375	2025-11-28 17:50:47.207375
00604900-70b2-4933-8673-b341bc296a9d	database	software	{"port": true, "vendor": true, "version": true}	2025-11-28 17:50:47.207375	2025-11-28 17:50:47.207375
0b6abd32-f818-4aa9-9a2c-c24c65fdb3cd	web_service	service	{"url": false, "port": true}	2025-11-28 17:50:47.207375	2025-11-28 17:50:47.207375
6fa48aa3-4ecd-48c5-8823-412846ba42e9	network_device	network	{"device_type": true, "ip_addresses": true}	2025-11-28 17:50:47.207375	2025-11-28 17:50:47.207375
e44ef5a6-c275-44a8-8be2-05ae46e10617	iot_device	hardware	{"device_type": true, "ip_addresses": false}	2025-11-28 17:50:47.207375	2025-11-28 17:50:47.207375
\.


--
-- Data for Name: cmdb_configuration_items; Type: TABLE DATA; Schema: public; Owner: claude
--

COPY public.cmdb_configuration_items (id, ci_type, ci_name, ci_description, owner, status, environment, hardware_specs, software_specs, ip_addresses, dns_names, ports, created_at, updated_at, discovered_at, last_verified_at) FROM stdin;
33603f34-e292-4091-9526-7c1d81aa407f	server	bluefin	PostgreSQL database hub, thermal memory host	it_triad	active	production	{"role": "database_hub", "services": ["postgresql", "thermal_memory", "zammad_db"]}	\N	{192.168.132.222,100.112.254.96}	\N	\N	2025-11-28 17:56:45.168895	2025-11-28 17:56:45.168895	\N	\N
75804262-ed64-409b-8bb0-983acd2ee039	server	redfin	GPU development node, IT Jrs workspace, SAG host	it_triad	active	production	{"gpu": "NVIDIA RTX 4090", "role": "gpu_dev", "services": ["sag", "visual_kanban", "grafana"]}	\N	{192.168.132.223,100.116.27.89}	\N	\N	2025-11-28 17:56:45.168895	2025-11-28 17:56:45.168895	\N	\N
3888cd33-496e-4718-bb25-573fc58c004d	server	greenfin	macOS local development	it_triad	active	development	{"os": "macOS", "role": "local_dev"}	\N	{192.168.132.224,100.100.243.116}	\N	\N	2025-11-28 17:56:45.168895	2025-11-28 17:56:45.168895	\N	\N
c0ce4ffd-a96f-4ec2-9b2e-9cda6b35a920	server	yellowfin	IoT legacy node	it_triad	active	production	{"role": "iot_legacy"}	\N	{192.168.132.221}	\N	\N	2025-11-28 17:56:45.168895	2025-11-28 17:56:45.168895	\N	\N
101dc084-f9a3-4052-b2cc-91f3d75ca777	server	bmasass	M4 Max MacBook Pro, mobile command post	command_post	active	production	{"os": "macOS", "cpu": "M4 Max", "role": "mobile_command_post"}	\N	{192.168.132.21,100.103.27.106}	\N	\N	2025-11-28 17:56:45.168895	2025-11-28 17:56:45.168895	\N	\N
3b0c4441-8ddc-49fe-8513-465b70de20ae	server	sasass	TBD node	it_triad	planned	production	{}	\N	{192.168.132.241}	\N	\N	2025-11-28 17:56:45.168895	2025-11-28 17:56:45.168895	\N	\N
ab9f2c05-c698-42b9-be5d-f2ad3e566285	server	sasass2	TBD node	it_triad	planned	production	{}	\N	{192.168.132.242}	\N	\N	2025-11-28 17:56:45.168895	2025-11-28 17:56:45.168895	\N	\N
b890ee62-dd5b-4660-92cb-e7674ec8dc94	database	postgresql_bluefin	PostgreSQL 17.6 on bluefin	it_triad	active	production	\N	{"vendor": "PostgreSQL", "version": "17.6", "databases": ["triad_federation", "zammad_production"]}	\N	\N	{5432}	2025-11-28 17:56:45.172693	2025-11-28 17:56:45.172693	\N	\N
757fd4de-4a46-4f7e-81f1-84f869f94fc6	web_service	sag_unified_interface	SAG Unified Interface	it_triad	active	production	\N	{"url": "http://192.168.132.223:4000", "framework": "python_web"}	\N	\N	{4000}	2025-11-28 17:56:45.172693	2025-11-28 17:56:45.172693	\N	\N
978b3dde-d3c0-4037-a8d5-7fba5b8b6cb1	web_service	visual_kanban	Visual Kanban Board	it_triad	active	production	\N	{"url": "http://192.168.132.223:8002", "framework": "python"}	\N	\N	{5000,8002,8765}	2025-11-28 17:56:45.172693	2025-11-28 17:56:45.172693	\N	\N
d4167745-bf4f-4003-ad89-05991f97d747	web_service	grafana	Grafana monitoring	it_triad	active	production	\N	{"url": "http://192.168.132.223:3000"}	\N	\N	{3000}	2025-11-28 17:56:45.172693	2025-11-28 17:56:45.172693	\N	\N
e6176483-9bf4-4690-9f93-948162fc26e7	iot_device	iot_device_1	IoT device (ID 1)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 1, "firmware_version": null, "management_capable": false, "management_protocol": null}	{192.168.132.242}	\N	{}	2025-11-29 00:02:07.69811	2025-11-29 00:13:36.619139	\N	\N
306283a1-ad8f-445d-a058-2902610eb366	iot_device	iot_device_1598	IoT device (ID 1598)	iot_sync	retired	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 1598, "firmware_version": null, "management_capable": false, "management_protocol": null}	{192.168.1.187}	\N	{}	2025-11-29 00:02:07.69811	2025-11-29 00:13:36.619139	\N	\N
19e3fd88-3f95-48a9-8d67-e81cedf92940	iot_device	device_10	IoT device (ID 2885)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2885, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.10}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
1fa22dfc-0526-4961-8632-7e9dfb7dbb8d	iot_device	device_11	IoT device (ID 2886)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2886, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.11}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
d98229dd-e9e7-4739-8fb6-c2b6dadc225d	iot_device	device_3	IoT device (ID 2887)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2887, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.3}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
6c685bd4-fe80-4fcb-b2db-001e86b41343	iot_device	device_14	IoT device (ID 2888)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2888, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.14}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
ae697bf1-e0cd-4ed5-a7a6-50478460ea7e	iot_device	device_15	IoT device (ID 2889)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2889, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.15}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
30656959-be80-4b1e-8983-4a7bafa3249e	iot_device	device_9	IoT device esp32(ID 2890)	iot_sync	active	production	\N	{"device_type": "esp32", "source_table": "zammad_production.iot_devices", "iot_device_id": 2890, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.9}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
242e73cc-dd2b-4830-aeaf-4e935537a813	iot_device	device_17	IoT device (ID 2891)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2891, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.17}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
21fe392b-5957-4188-be97-313a046ff12a	iot_device	device_18	IoT device (ID 2892)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2892, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.18}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
d4a7a536-99a9-45c4-bc06-2938b8886463	iot_device	device_2	IoT device (ID 2893)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2893, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.2}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
d60fa491-cee8-45fa-b597-62f285911272	iot_device	device_19	IoT device (ID 2894)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2894, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.19}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
3b65450d-6842-4aa8-a051-8e2b1dc5d0fe	iot_device	device_21	IoT device (ID 2895)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2895, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.21}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
ffc103fe-759a-444d-947d-1d8cfe5b82e2	iot_device	device_24	IoT device (ID 2896)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2896, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.24}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
3632b9e6-c158-4750-b8b3-9e0704d81a3e	iot_device	device_22	IoT device (ID 2897)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2897, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.22}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
892c4443-4fff-4a53-8fb6-78b78e4f79b0	iot_device	device_25	IoT device (ID 2898)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2898, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.25}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
6565d02f-923a-4435-bbad-44ae58e13ba1	iot_device	device_4	IoT device (ID 2899)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2899, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.4}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
921a1ad9-1c14-40fd-afd1-34c0d9ccbea3	iot_device	device_32	IoT device (ID 2900)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2900, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.32}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
9b286013-7b78-4487-bfbb-8bd95fd39839	iot_device	device_5	IoT device (ID 2901)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2901, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.5}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
5ee7882d-0cab-4388-bffa-7859461f7dfd	iot_device	device_26	IoT device (ID 2902)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2902, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.26}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
e818b2d3-4533-4f26-b23b-1bc8e2b4cafd	iot_device	device_36	IoT device (ID 2903)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2903, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.36}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
6f2f6bb1-c94f-4ca2-bb35-e94ba1abfe52	iot_device	device_8	IoT device (ID 2904)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2904, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.8}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
c9c0b24d-5d8c-471f-bbdb-7fe8a17f8e8c	iot_device	device_29	IoT device (ID 2905)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2905, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.29}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
c45a34c3-7cba-4544-b57c-de0a8b648735	iot_device	device_38	IoT device (ID 2906)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2906, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.38}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
7aa5d785-fb0d-4c5c-b944-21eca1208fce	iot_device	device_76	IoT device (ID 2907)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2907, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.76}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
41cd1916-fa37-4867-90ec-a95b2eb79936	iot_device	_gateway	IoT device (ID 2908)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2908, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.1}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
4caf7476-e0cc-4e06-8297-b3eb02890cae	iot_device	device_74	IoT device (ID 2909)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2909, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.74}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
112ba1fb-c208-4fa9-a0bc-6c1da64b86c9	iot_device	device_71	IoT device (ID 2910)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2910, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.71}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
5afdaa20-8f56-44c4-9191-692df92633af	iot_device	device_90	IoT device (ID 2911)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2911, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.90}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
d5d1de77-ef26-4486-829b-8f6ce4650bb4	iot_device	device_89	IoT device (ID 2912)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2912, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.89}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
ae69c3e9-0965-4d56-bf48-490be1e117fb	iot_device	device_108	IoT device (ID 2913)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2913, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.108}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
b84c2bb3-588f-4e59-ab9a-15d7765abd72	iot_device	device_77	IoT device (ID 2914)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2914, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.77}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
00737058-7fb4-49b1-8735-24e6027126e5	iot_device	device_27	IoT device (ID 2915)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2915, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.27}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
0ea92a46-88ea-4a2f-8dee-853d3ab05ee7	iot_device	device_113	IoT device (ID 2916)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2916, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.113}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
75c34485-0562-4592-995a-8e8421047228	iot_device	device_13	IoT device (ID 2917)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2917, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.13}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
b71ff4e1-90c3-4574-a84e-cc15cfb97952	iot_device	device_28	IoT device (ID 2918)	iot_sync	active	production	\N	{"device_type": "unknown", "source_table": "zammad_production.iot_devices", "iot_device_id": 2918, "firmware_version": null, "management_capable": false, "management_protocol": null}	{10.0.0.28}	\N	{}	2025-11-29 00:13:36.619139	2025-11-29 00:13:36.619139	\N	\N
\.


--
-- Data for Name: cmdb_relationships; Type: TABLE DATA; Schema: public; Owner: claude
--

COPY public.cmdb_relationships (id, relationship_type, source_node, target_node, description, temperature, created_at) FROM stdin;
92ddcb4a-2576-4441-9170-3d839cb55ce7	depends_on	greenfin	bluefin	Greenfin Trading Jr and Flow Monitor Jr depend on bluefin PostgreSQL hub for data sync	78.5	2025-11-10 23:10:56.372414
2873d1f7-da4b-4ee6-a4c2-f2fe532a90e6	syncs_with	greenfin	bluefin	Bidirectional PostgreSQL sync: trading_decisions, flow_monitor_data, constitutional knowledge	78.5	2025-11-10 23:10:56.378297
51ad4530-efcd-40e7-a719-df331cb99c61	runs_on	sag_unified_interface	redfin	SAG Unified Interface web service running on redfin port 4000	70	2025-11-28 18:18:45.099605
0c794a57-0fa1-44f7-a62a-b6f45b21e34b	runs_on	visual_kanban	redfin	Visual Kanban Board service running on redfin port 8002	70	2025-11-28 18:18:45.099605
ed0e5aa4-c951-4322-8d28-404fd82264cb	runs_on	grafana	redfin	Grafana monitoring dashboard running on redfin port 3000	70	2025-11-28 18:18:45.099605
358dc594-c49c-4989-b629-0ff59183116d	runs_on	postgresql	bluefin	PostgreSQL database service running on bluefin port 5432	75	2025-11-28 18:18:45.099605
66baf871-e7ec-44f2-82e9-b5469e559fdc	depends_on	sag_unified_interface	postgresql	SAG queries triad_federation and zammad_production databases	75	2025-11-28 18:18:45.099605
703f34ed-791a-4a7d-93e9-22202cfb8546	depends_on	visual_kanban	postgresql	Visual Kanban reads from triad_federation database	75	2025-11-28 18:18:45.099605
371fb73b-2814-4bf9-b53f-a7028aa09b40	depends_on	grafana	redfin	Grafana depends on redfin for hosting and storage	70	2025-11-28 18:18:45.099605
\.


--
-- Data for Name: cmdb_service_dependencies; Type: TABLE DATA; Schema: public; Owner: claude
--

COPY public.cmdb_service_dependencies (id, service_ci_id, depends_on_ci_id, dependency_type, criticality, created_at) FROM stdin;
\.


--
-- Name: cmdb_changes cmdb_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_changes
    ADD CONSTRAINT cmdb_changes_pkey PRIMARY KEY (id);


--
-- Name: cmdb_ci_types cmdb_ci_types_pkey; Type: CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_ci_types
    ADD CONSTRAINT cmdb_ci_types_pkey PRIMARY KEY (id);


--
-- Name: cmdb_ci_types cmdb_ci_types_type_name_key; Type: CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_ci_types
    ADD CONSTRAINT cmdb_ci_types_type_name_key UNIQUE (type_name);


--
-- Name: cmdb_configuration_items cmdb_configuration_items_ci_name_key; Type: CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_configuration_items
    ADD CONSTRAINT cmdb_configuration_items_ci_name_key UNIQUE (ci_name);


--
-- Name: cmdb_configuration_items cmdb_configuration_items_pkey; Type: CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_configuration_items
    ADD CONSTRAINT cmdb_configuration_items_pkey PRIMARY KEY (id);


--
-- Name: cmdb_relationships cmdb_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_relationships
    ADD CONSTRAINT cmdb_relationships_pkey PRIMARY KEY (id);


--
-- Name: cmdb_service_dependencies cmdb_service_dependencies_pkey; Type: CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_service_dependencies
    ADD CONSTRAINT cmdb_service_dependencies_pkey PRIMARY KEY (id);


--
-- Name: idx_change_type; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_change_type ON public.cmdb_changes USING btree (change_type);


--
-- Name: idx_changes_type; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_changes_type ON public.cmdb_changes USING btree (change_type);


--
-- Name: idx_ci_environment; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_ci_environment ON public.cmdb_configuration_items USING btree (environment);


--
-- Name: idx_ci_name; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_ci_name ON public.cmdb_configuration_items USING btree (ci_name);


--
-- Name: idx_ci_owner; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_ci_owner ON public.cmdb_configuration_items USING btree (owner);


--
-- Name: idx_ci_status; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_ci_status ON public.cmdb_configuration_items USING btree (status);


--
-- Name: idx_ci_type; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_ci_type ON public.cmdb_configuration_items USING btree (ci_type);


--
-- Name: idx_ci_updated; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_ci_updated ON public.cmdb_configuration_items USING btree (updated_at);


--
-- Name: idx_cmdb_changes_node; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_cmdb_changes_node ON public.cmdb_changes USING btree (node_name);


--
-- Name: idx_rel_type; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_rel_type ON public.cmdb_relationships USING btree (relationship_type);


--
-- Name: idx_relationship_type; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_relationship_type ON public.cmdb_relationships USING btree (relationship_type);


--
-- Name: idx_service_deps_depends; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_service_deps_depends ON public.cmdb_service_dependencies USING btree (depends_on_ci_id);


--
-- Name: idx_service_deps_service; Type: INDEX; Schema: public; Owner: claude
--

CREATE INDEX idx_service_deps_service ON public.cmdb_service_dependencies USING btree (service_ci_id);


--
-- Name: cmdb_configuration_items trigger_update_ci_timestamp; Type: TRIGGER; Schema: public; Owner: claude
--

CREATE TRIGGER trigger_update_ci_timestamp BEFORE UPDATE ON public.cmdb_configuration_items FOR EACH ROW EXECUTE FUNCTION public.update_cmdb_ci_timestamp();


--
-- Name: cmdb_changes cmdb_changes_node_name_fkey; Type: FK CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_changes
    ADD CONSTRAINT cmdb_changes_node_name_fkey FOREIGN KEY (node_name) REFERENCES public.cmdb_hardware(node_name);


--
-- Name: cmdb_service_dependencies cmdb_service_dependencies_depends_on_ci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_service_dependencies
    ADD CONSTRAINT cmdb_service_dependencies_depends_on_ci_id_fkey FOREIGN KEY (depends_on_ci_id) REFERENCES public.cmdb_configuration_items(id);


--
-- Name: cmdb_service_dependencies cmdb_service_dependencies_service_ci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: claude
--

ALTER TABLE ONLY public.cmdb_service_dependencies
    ADD CONSTRAINT cmdb_service_dependencies_service_ci_id_fkey FOREIGN KEY (service_ci_id) REFERENCES public.cmdb_configuration_items(id);


--
-- Name: TABLE cmdb_changes; Type: ACL; Schema: public; Owner: claude
--

GRANT ALL ON TABLE public.cmdb_changes TO cherokee;


--
-- Name: TABLE cmdb_relationships; Type: ACL; Schema: public; Owner: claude
--

GRANT ALL ON TABLE public.cmdb_relationships TO cherokee;


--
-- PostgreSQL database dump complete
--

\unrestrict WZGcSeoZPcBZe1RWZyKNcDdi2AlLz6L7U4n5kUcIvEe3jBbqPAhGcZbBrQFYVqF

