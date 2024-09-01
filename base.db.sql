BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "car" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "engineer" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT,
	"phone_number"	INTEGER NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "status" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "route" (
	"route_id"	INTEGER NOT NULL UNIQUE,
	"info"	TEXT,
	"result"	TEXT,
	"engineer" INTEGER,
	"status" INTEGER,
	"date_created" TEXT,
	"date_sent" TEXT,
	"command_car" INTEGER,
	"chat_id" INTEGER,
	FOREIGN KEY ("engineer") REFERENCES "engineer(id)",
	FOREIGN KEY ("status") REFERENCES "status(id)",
	FOREIGN KEY ("command_car") REFERENCES "car(id)",
	PRIMARY KEY("route_id")
);
CREATE TABLE IF NOT EXISTS "photo" (
	"id"	INTEGER NOT NULL UNIQUE,
	"filename"	TEXT NOT NULL UNIQUE,
	"route" INTEGER,
	"car" INTEGER,
	"photo_type" INTEGER,
	FOREIGN KEY ("route") REFERENCES "route(route_id)"
	FOREIGN KEY("car") REFERENCES "car(id)",
	FOREIGN KEY("photo_type") REFERENCES "photo_type(id)",
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "photo_type" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY ("id" AUTOINCREMENT)
);
COMMIT;