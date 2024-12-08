CREATE TABLE Category (
    mainCategory VARCHAR(50),
    subCategory VARCHAR(50),
    catNotes TEXT,
    PRIMARY KEY (mainCategory, subCategory)
);

CREATE TABLE Item (
    itemID INT AUTO_INCREMENT,
    iDescription TEXT,
    photo BLOB,
    color VARCHAR(30),
    isNew BOOLEAN,
    hasPieces BOOLEAN,
    material VARCHAR(50),
    mainCategory VARCHAR(50),
    subCategory VARCHAR(50),
    PRIMARY KEY (itemID),
    FOREIGN KEY (mainCategory, subCategory) REFERENCES Category(mainCategory, subCategory)
);

CREATE TABLE Person (
    cid INT AUTO_INCREMENT UNIQUE,
    userName VARCHAR(50),
    password VARCHAR(255),
    fname VARCHAR(50),
    lname VARCHAR(50),
    email VARCHAR(100),
    PRIMARY KEY (userName)
);

CREATE TABLE PersonPhone (
    userName VARCHAR(50),
    phone VARCHAR(20),
    PRIMARY KEY (userName, phone),
    FOREIGN KEY (userName) REFERENCES Person(userName)
);

CREATE TABLE DonatedBy (
    itemID INT,
    userName VARCHAR(50),
    donateDate DATE,
    PRIMARY KEY (itemID, userName),
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (userName) REFERENCES Person(userName)
);

CREATE TABLE Role (
    roleID INT AUTO_INCREMENT,
    rDescription TEXT,
    PRIMARY KEY (roleID)
);

CREATE TABLE Act (
    userName VARCHAR(50),
    roleID INT,
    PRIMARY KEY (userName, roleID),
    FOREIGN KEY (userName) REFERENCES Person(userName),
    FOREIGN KEY (roleID) REFERENCES Role(roleID)
);

CREATE TABLE Location (
    roomNum INT,
    shelfNum INT,
    shelfDescription TEXT,
    PRIMARY KEY (roomNum, shelfNum)
);

CREATE TABLE Piece (
    itemID INT,
    pieceNum INT,
    pDescription TEXT,
    length FLOAT,
    width FLOAT,
    height FLOAT,
    roomNum INT,
    shelfNum INT,
    pNotes TEXT,
    PRIMARY KEY (itemID, pieceNum),
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (roomNum, shelfNum) REFERENCES Location(roomNum, shelfNum)
);

CREATE TABLE Ordered (
    orderID INT AUTO_INCREMENT,
    orderDate DATE,
    orderNotes TEXT,
    supervisor VARCHAR(50),
    client VARCHAR(50),
    PRIMARY KEY (orderID),
    FOREIGN KEY (supervisor) REFERENCES Person(userName),
    FOREIGN KEY (client) REFERENCES Person(userName)
);
CREATE TABLE ItemIn (
    itemID INT,
    orderID INT,
    found BOOLEAN,
    PRIMARY KEY (itemID, orderID),
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (orderID) REFERENCES Ordered(orderID)
);

CREATE TABLE Delivered (
    userName VARCHAR(50),
    orderID INT,
    status VARCHAR(20),
    date DATE,
    PRIMARY KEY (userName, orderID),
    FOREIGN KEY (userName) REFERENCES Person(userName),
    FOREIGN KEY (orderID) REFERENCES Ordered(orderID)
);

INSERT INTO role(rDescription)
VALUES ('Staff'), ('Donor'), ('Volunteer'), ('Client');

INSERT INTO location(roomNum,shelfNum) 
VALUES (1,1),(1,2),(2,1),(2,2)



INSERT INTO piece(itemID,pieceNum,roomNum,shelfNum) 
VALUES (2, 1, 1, 1)

DELIMITER $$

CREATE TRIGGER set_piece_num
BEFORE INSERT ON piece
FOR EACH ROW
BEGIN
    DECLARE maxPieceNum INT;

    IF NEW.pieceNum IS NULL THEN
        SELECT COALESCE(MAX(pieceNum), 0) INTO maxPieceNum
        FROM piece
        WHERE itemID = NEW.itemID;
        SET NEW.pieceNum = maxPieceNum + 1;
    END IF;
END$$

DELIMITER ;



