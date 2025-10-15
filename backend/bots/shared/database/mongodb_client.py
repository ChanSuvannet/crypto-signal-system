
# ============================================
# Crypto Trading Signal System
# backed/bots/shared/database/mongodb_client.py
# Deception: Async MongoDB client for ML models and unstructured data.
# ============================================

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import PyMongoError

from ..core.config import Config
from ..core.logger import get_logger
from ..core.exceptions import (
    BotConnectionError,
    BotDatabaseError,
    retry_on_error
)


class MongoDBClient:
    """
    Async MongoDB client for document storage.
    
    Features:
    - Document CRUD operations
    - Aggregation pipelines
    - GridFS for large files
    - Index management
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize MongoDB client.
        
        Args:
            config: Configuration instance
        """
        self.config = config or Config()
        self.logger = get_logger('mongodb_client')
        
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False
    
    async def connect(self):
        """Establish MongoDB connection."""
        if self._is_connected:
            self.logger.warning("MongoDB client is already connected")
            return
        
        try:
            # Get MongoDB URL
            mongo_url = self.config.get_database_url('mongodb')
            
            # Create MongoDB client
            self.client = AsyncIOMotorClient(
                mongo_url,
                maxPoolSize=self.config.get('DB_POOL_MAX', 10),
                minPoolSize=self.config.get('DB_POOL_MIN', 2),
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            
            # Get database
            self.db = self.client[self.config.get('MONGO_DATABASE')]
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Get server info
            server_info = await self.client.server_info()
            
            self._is_connected = True
            self.logger.info(f"✓ Connected to MongoDB {server_info['version']}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise BotConnectionError(
                f"MongoDB connection failed: {str(e)}",
                service="MongoDB"
            )
    
    async def disconnect(self):
        """Close MongoDB connection."""
        if not self._is_connected:
            return
        
        try:
            if self.client:
                self.client.close()
            
            self._is_connected = False
            self.logger.info("✓ Disconnected from MongoDB")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from MongoDB: {e}")
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """
        Get collection by name.
        
        Args:
            collection_name: Collection name
            
        Returns:
            Collection instance
        """
        if not self._is_connected:
            raise BotConnectionError("MongoDB not connected")
        
        return self.db[collection_name]
    
    @retry_on_error(max_attempts=3)
    async def insert_one(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> str:
        """
        Insert single document.
        
        Args:
            collection: Collection name
            document: Document to insert
            
        Returns:
            Inserted document ID
        """
        try:
            # Add timestamp if not present
            if 'created_at' not in document:
                document['created_at'] = datetime.utcnow()
            
            coll = self.get_collection(collection)
            result = await coll.insert_one(document)
            return str(result.inserted_id)
            
        except PyMongoError as e:
            self.logger.error(f"Insert one failed: {e}")
            raise BotDatabaseError(f"MongoDB insert failed: {str(e)}")
    
    @retry_on_error(max_attempts=3)
    async def insert_many(
        self,
        collection: str,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Insert multiple documents.
        
        Args:
            collection: Collection name
            documents: List of documents
            
        Returns:
            List of inserted document IDs
        """
        try:
            # Add timestamps
            for doc in documents:
                if 'created_at' not in doc:
                    doc['created_at'] = datetime.utcnow()
            
            coll = self.get_collection(collection)
            result = await coll.insert_many(documents)
            return [str(id) for id in result.inserted_ids]
            
        except PyMongoError as e:
            self.logger.error(f"Insert many failed: {e}")
            raise BotDatabaseError(f"MongoDB bulk insert failed: {str(e)}")
    
    @retry_on_error(max_attempts=3)
    async def find_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find single document.
        
        Args:
            collection: Collection name
            filter: Query filter
            projection: Fields to include/exclude
            
        Returns:
            Document or None
        """
        try:
            coll = self.get_collection(collection)
            document = await coll.find_one(filter, projection)
            
            if document and '_id' in document:
                document['_id'] = str(document['_id'])
            
            return document
            
        except PyMongoError as e:
            self.logger.error(f"Find one failed: {e}")
            raise BotDatabaseError(f"MongoDB find failed: {str(e)}")
    
    @retry_on_error(max_attempts=3)
    async def find_many(
        self,
        collection: str,
        filter: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents.
        
        Args:
            collection: Collection name
            filter: Query filter
            projection: Fields to include/exclude
            sort: Sort specification
            limit: Maximum number of documents
            skip: Number of documents to skip
            
        Returns:
            List of documents
        """
        try:
            coll = self.get_collection(collection)
            cursor = coll.find(filter or {}, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            return documents
            
        except PyMongoError as e:
            self.logger.error(f"Find many failed: {e}")
            raise BotDatabaseError(f"MongoDB find failed: {str(e)}")
    
    @retry_on_error(max_attempts=3)
    async def update_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        """
        Update single document.
        
        Args:
            collection: Collection name
            filter: Query filter
            update: Update operations
            upsert: Insert if not exists
            
        Returns:
            Number of documents modified
        """
        try:
            # Add updated_at timestamp
            if '$set' in update:
                update['$set']['updated_at'] = datetime.utcnow()
            else:
                update = {'$set': {**update, 'updated_at': datetime.utcnow()}}
            
            coll = self.get_collection(collection)
            result = await coll.update_one(filter, update, upsert=upsert)
            return result.modified_count
            
        except PyMongoError as e:
            self.logger.error(f"Update one failed: {e}")
            raise BotDatabaseError(f"MongoDB update failed: {str(e)}")
    
    @retry_on_error(max_attempts=3)
    async def update_many(
        self,
        collection: str,
        filter: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """
        Update multiple documents.
        
        Args:
            collection: Collection name
            filter: Query filter
            update: Update operations
            
        Returns:
            Number of documents modified
        """
        try:
            # Add updated_at timestamp
            if '$set' in update:
                update['$set']['updated_at'] = datetime.utcnow()
            else:
                update = {'$set': {**update, 'updated_at': datetime.utcnow()}}
            
            coll = self.get_collection(collection)
            result = await coll.update_many(filter, update)
            return result.modified_count
            
        except PyMongoError as e:
            self.logger.error(f"Update many failed: {e}")
            raise BotDatabaseError(f"MongoDB bulk update failed: {str(e)}")
    
    @retry_on_error(max_attempts=3)
    async def delete_one(
        self,
        collection: str,
        filter: Dict[str, Any]
    ) -> int:
        """
        Delete single document.
        
        Args:
            collection: Collection name
            filter: Query filter
            
        Returns:
            Number of documents deleted
        """
        try:
            coll = self.get_collection(collection)
            result = await coll.delete_one(filter)
            return result.deleted_count
            
        except PyMongoError as e:
            self.logger.error(f"Delete one failed: {e}")
            raise BotDatabaseError(f"MongoDB delete failed: {str(e)}")
    
    @retry_on_error(max_attempts=3)
    async def delete_many(
        self,
        collection: str,
        filter: Dict[str, Any]
    ) -> int:
        """
        Delete multiple documents.
        
        Args:
            collection: Collection name
            filter: Query filter
            
        Returns:
            Number of documents deleted
        """
        try:
            coll = self.get_collection(collection)
            result = await coll.delete_many(filter)
            return result.deleted_count
            
        except PyMongoError as e:
            self.logger.error(f"Delete many failed: {e}")
            raise BotDatabaseError(f"MongoDB bulk delete failed: {str(e)}")
    
    async def count(
        self,
        collection: str,
        filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count documents.
        
        Args:
            collection: Collection name
            filter: Query filter
            
        Returns:
            Number of documents
        """
        try:
            coll = self.get_collection(collection)
            return await coll.count_documents(filter or {})
            
        except PyMongoError as e:
            self.logger.error(f"Count failed: {e}")
            raise BotDatabaseError(f"MongoDB count failed: {str(e)}")
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute aggregation pipeline.
        
        Args:
            collection: Collection name
            pipeline: Aggregation pipeline
            
        Returns:
            Aggregation results
        """
        try:
            coll = self.get_collection(collection)
            cursor = coll.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            # Convert ObjectId to string
            for doc in results:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            return results
            
        except PyMongoError as e:
            self.logger.error(f"Aggregation failed: {e}")
            raise BotDatabaseError(f"MongoDB aggregation failed: {str(e)}")
    
    async def create_index(
        self,
        collection: str,
        keys: List[tuple],
        unique: bool = False,
        name: Optional[str] = None
    ):
        """
        Create index on collection.
        
        Args:
            collection: Collection name
            keys: Index keys [(field, direction), ...]
            unique: Whether index should be unique
            name: Index name
        """
        try:
            coll = self.get_collection(collection)
            await coll.create_index(keys, unique=unique, name=name)
            self.logger.info(f"Created index on {collection}")
            
        except PyMongoError as e:
            self.logger.error(f"Create index failed: {e}")
            raise BotDatabaseError(f"MongoDB create index failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MongoDB health."""
        try:
            # Ping
            await self.client.admin.command('ping')
            
            # Get server info
            server_info = await self.client.server_info()
            
            # Get database stats
            stats = await self.db.command('dbStats')
            
            return {
                'healthy': True,
                'connected': self._is_connected,
                'version': server_info['version'],
                'collections': stats['collections'],
                'data_size': stats.get('dataSize', 0),
                'storage_size': stats.get('storageSize', 0),
            }
        except Exception as e:
            return {
                'healthy': False,
                'connected': False,
                'error': str(e)
            }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
