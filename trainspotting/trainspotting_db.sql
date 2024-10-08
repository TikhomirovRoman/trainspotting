BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "car" (
	"id"	INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"name"	TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "engineer" (
	"id"	INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"name"	TEXT,
	"phone_number"	TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "status" (
	"id"	INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"name"	TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "route"(
	"route_id"	INTEGER PRIMARY KEY,
	"info"	TEXT,
	"result"	TEXT,
	"engineer" INTEGER,
	"status" INTEGER,
	"date_created" TEXT,
	"date_sent" TEXT,
	"command_car" INTEGER,
	"chat_id" INTEGER,
    CONSTRAINT "route_constraints"
	    FOREIGN KEY ("engineer") REFERENCES engineer(id),
	    FOREIGN KEY ("status") REFERENCES status(id),
	    FOREIGN KEY ("command_car") REFERENCES car(id)
);

CREATE TABLE IF NOT EXISTS "photo_type" (
	"id"	INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"name"	TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS "photo" (
	"id"	INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	"filename"	TEXT NOT NULL UNIQUE,
	"route" INTEGER REFERENCES route(route_id),
	"car" INTEGER REFERENCES car(id),
	"photo_type" INTEGER REFERENCES photo_type(id) ON DELETE CASCADE
);
COMMIT;
