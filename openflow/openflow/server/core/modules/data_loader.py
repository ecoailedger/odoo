"""
Data Loader

Loads module data files (CSV and XML) into the database.
"""
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Loads data files from modules

    Supports:
    - CSV files (security/ir.model.access.csv)
    - XML files (data/*.xml, views/*.xml)
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize data loader

        Args:
            session: Database session for loading data
        """
        self.session = session
        self._xml_ids: Dict[str, int] = {}  # External ID to database ID mapping

    async def load_csv_file(self, file_path: Path, model_name: str):
        """
        Load a CSV file into the database

        Args:
            file_path: Path to CSV file
            model_name: Model to load data into
        """
        logger.info(f"Loading CSV file: {file_path}")

        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                records = list(reader)

            logger.info(f"Loaded {len(records)} records from {file_path.name}")

            # TODO: Create records in database
            # This requires integration with the ORM
            for record in records:
                logger.debug(f"Record: {record}")

        except Exception as e:
            logger.error(f"Failed to load CSV file {file_path}: {e}")
            raise

    async def load_xml_file(self, file_path: Path, module_name: str):
        """
        Load an XML data file

        Args:
            file_path: Path to XML file
            module_name: Name of the module this file belongs to
        """
        logger.info(f"Loading XML file: {file_path}")

        if not file_path.exists():
            logger.warning(f"XML file not found: {file_path}")
            return

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Process <data> elements
            for data_elem in root.findall('data'):
                noupdate = data_elem.get('noupdate', '0') == '1'

                # Process <record> elements
                for record_elem in data_elem.findall('record'):
                    await self._process_record(
                        record_elem,
                        module_name,
                        noupdate
                    )

        except Exception as e:
            logger.error(f"Failed to load XML file {file_path}: {e}")
            raise

    async def _process_record(
        self,
        record_elem: ET.Element,
        module_name: str,
        noupdate: bool
    ):
        """
        Process a <record> element from XML

        Args:
            record_elem: XML element for the record
            module_name: Module name for external ID namespacing
            noupdate: If True, don't update existing records
        """
        record_id = record_elem.get('id')
        model_name = record_elem.get('model')

        if not record_id or not model_name:
            logger.warning("Record missing id or model attribute")
            return

        # Build external ID (module.id)
        external_id = f"{module_name}.{record_id}"

        # Extract field values
        values = {}
        for field_elem in record_elem.findall('field'):
            field_name = field_elem.get('name')
            if not field_name:
                continue

            # Get field value
            field_value = self._parse_field_value(field_elem)
            values[field_name] = field_value

        logger.debug(f"Processing record {external_id} ({model_name}): {values}")

        # TODO: Create or update record in database
        # This requires integration with the ORM

    def _parse_field_value(self, field_elem: ET.Element) -> Any:
        """
        Parse field value from XML element

        Args:
            field_elem: XML field element

        Returns:
            Parsed field value
        """
        # Check for 'eval' attribute (Python expression)
        if field_elem.get('eval'):
            eval_expr = field_elem.get('eval')
            # TODO: Safely evaluate Python expressions
            # For now, return as string
            return eval_expr

        # Check for 'ref' attribute (external ID reference)
        if field_elem.get('ref'):
            ref_id = field_elem.get('ref')
            # TODO: Resolve external ID to database ID
            return ref_id

        # Plain text value
        return field_elem.text or ''

    async def load_module_data(self, module_path: Path, module_name: str, data_files: List[str]):
        """
        Load all data files for a module

        Args:
            module_path: Path to module directory
            module_name: Name of the module
            data_files: List of data file paths (relative to module)
        """
        logger.info(f"Loading data for module: {module_name}")

        for data_file in data_files:
            file_path = module_path / data_file

            if not file_path.exists():
                logger.warning(f"Data file not found: {file_path}")
                continue

            # Determine file type and load
            if file_path.suffix == '.csv':
                # Extract model name from path (e.g., security/ir.model.access.csv -> ir.model.access)
                model_name = file_path.stem.replace('.', '_')
                await self.load_csv_file(file_path, model_name)
            elif file_path.suffix == '.xml':
                await self.load_xml_file(file_path, module_name)
            else:
                logger.warning(f"Unknown data file type: {file_path}")

        logger.info(f"Finished loading data for module: {module_name}")


class ExternalIdManager:
    """
    Manages external IDs (XML IDs) for data records

    External IDs allow referring to records across modules using
    a stable identifier (module.xml_id) instead of database IDs.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize external ID manager

        Args:
            session: Database session
        """
        self.session = session
        self._cache: Dict[str, int] = {}

    async def get_id(self, external_id: str) -> Optional[int]:
        """
        Get database ID for an external ID

        Args:
            external_id: External ID in format 'module.xml_id'

        Returns:
            Database ID or None if not found
        """
        # Check cache first
        if external_id in self._cache:
            return self._cache[external_id]

        # TODO: Query ir.model.data table
        # For now, return None
        return None

    async def set_id(self, external_id: str, model: str, db_id: int):
        """
        Register an external ID mapping

        Args:
            external_id: External ID in format 'module.xml_id'
            model: Model name
            db_id: Database ID
        """
        self._cache[external_id] = db_id

        # TODO: Insert into ir.model.data table
        logger.debug(f"Registered external ID: {external_id} -> {model}({db_id})")

    def resolve_ref(self, ref: str) -> Optional[int]:
        """
        Resolve a reference (external ID) to a database ID

        Args:
            ref: External ID or direct database ID

        Returns:
            Database ID or None
        """
        # If it's a number, return it directly
        try:
            return int(ref)
        except ValueError:
            pass

        # Otherwise, look up the external ID
        return self._cache.get(ref)
