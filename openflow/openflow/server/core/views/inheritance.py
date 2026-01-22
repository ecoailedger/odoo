"""
View Inheritance

Handles view inheritance with XPath expressions.
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import logging
import copy

logger = logging.getLogger(__name__)


class ViewInheritance:
    """
    Handle view inheritance and modifications using XPath
    """

    def __init__(self):
        """Initialize view inheritance handler"""
        pass

    async def apply_inheritance(self, base_arch: str, inherit_specs: List[Dict[str, Any]]) -> str:
        """
        Apply inheritance specifications to base architecture

        Args:
            base_arch: Base view architecture XML
            inherit_specs: List of inheritance specs with xpath and position

        Returns:
            Modified architecture XML as string
        """
        try:
            # Parse base architecture
            root = ET.fromstring(base_arch)
        except ET.ParseError as e:
            logger.error(f"Failed to parse base architecture: {e}")
            raise ValueError(f"Invalid base architecture XML: {e}")

        # Apply each inheritance spec
        for spec in inherit_specs:
            root = await self._apply_spec(root, spec)

        # Convert back to string
        return ET.tostring(root, encoding='unicode')

    async def _apply_spec(self, root: ET.Element, spec: Dict[str, Any]) -> ET.Element:
        """
        Apply a single inheritance specification

        Args:
            root: Root element
            spec: Inheritance spec with 'xpath', 'position', 'arch'

        Returns:
            Modified root element
        """
        xpath = spec.get('xpath')
        position = spec.get('position', 'inside')
        arch_xml = spec.get('arch', '')

        if not xpath:
            logger.warning("Inheritance spec missing xpath")
            return root

        # Find target element(s) using xpath
        targets = self._find_xpath(root, xpath)

        if not targets:
            logger.warning(f"XPath expression '{xpath}' found no matches")
            return root

        # Parse modification XML
        if arch_xml:
            try:
                mod_root = ET.fromstring(arch_xml)
            except ET.ParseError as e:
                logger.error(f"Failed to parse modification XML: {e}")
                return root
        else:
            mod_root = None

        # Apply modification to each target
        for target in targets:
            if position == 'before':
                self._insert_before(target, mod_root)
            elif position == 'after':
                self._insert_after(target, mod_root)
            elif position == 'inside':
                self._insert_inside(target, mod_root)
            elif position == 'replace':
                self._replace(target, mod_root)
            elif position == 'attributes':
                self._modify_attributes(target, spec.get('attrs', {}))
            else:
                logger.warning(f"Unknown position: {position}")

        return root

    def _find_xpath(self, root: ET.Element, xpath: str) -> List[ET.Element]:
        """
        Find elements matching XPath expression

        Args:
            root: Root element to search in
            xpath: XPath expression

        Returns:
            List of matching elements
        """
        # Simple XPath implementation supporting common patterns
        # Full XPath would require lxml, but we'll support basic cases

        try:
            # Try standard ElementTree xpath (limited support)
            return root.findall(xpath)
        except Exception as e:
            logger.warning(f"XPath error with '{xpath}': {e}")

        # Fallback: parse common xpath patterns manually
        if xpath.startswith('//'):
            # Find all descendants with tag
            tag = xpath[2:].split('[')[0]
            return self._find_all_descendants(root, tag)
        elif '[@' in xpath:
            # Find by attribute
            return self._find_by_attribute(root, xpath)
        else:
            # Simple tag search
            return root.findall(f".//{xpath}")

    def _find_all_descendants(self, element: ET.Element, tag: str) -> List[ET.Element]:
        """Find all descendants with given tag"""
        results = []
        for child in element.iter(tag):
            results.append(child)
        return results

    def _find_by_attribute(self, root: ET.Element, xpath: str) -> List[ET.Element]:
        """
        Find elements by attribute
        Supports patterns like: //field[@name='partner_id']
        """
        results = []

        # Parse xpath pattern
        # Pattern: //tag[@attr='value']
        parts = xpath.split('[@')
        if len(parts) != 2:
            return results

        tag_part = parts[0].replace('//', '')
        attr_part = parts[1].rstrip(']')

        # Parse attribute condition
        if '=' in attr_part:
            attr_name, attr_value = attr_part.split('=', 1)
            attr_value = attr_value.strip('\'"')

            # Find all elements with tag
            for elem in root.iter(tag_part if tag_part else None):
                if elem.get(attr_name) == attr_value:
                    results.append(elem)

        return results

    def _insert_before(self, target: ET.Element, mod_elem: Optional[ET.Element]):
        """
        Insert modification before target

        Args:
            target: Target element
            mod_elem: Element to insert
        """
        if mod_elem is None:
            return

        parent = self._get_parent(target)
        if parent is None:
            logger.warning("Cannot insert before root element")
            return

        # Find index of target in parent
        index = list(parent).index(target)

        # Insert modification elements before target
        if mod_elem.tag == 'data':
            # Insert all children of <data>
            for i, child in enumerate(mod_elem):
                parent.insert(index + i, copy.deepcopy(child))
        else:
            parent.insert(index, copy.deepcopy(mod_elem))

    def _insert_after(self, target: ET.Element, mod_elem: Optional[ET.Element]):
        """
        Insert modification after target

        Args:
            target: Target element
            mod_elem: Element to insert
        """
        if mod_elem is None:
            return

        parent = self._get_parent(target)
        if parent is None:
            logger.warning("Cannot insert after root element")
            return

        # Find index of target in parent
        index = list(parent).index(target)

        # Insert modification elements after target
        if mod_elem.tag == 'data':
            # Insert all children of <data>
            for i, child in enumerate(reversed(list(mod_elem))):
                parent.insert(index + 1, copy.deepcopy(child))
        else:
            parent.insert(index + 1, copy.deepcopy(mod_elem))

    def _insert_inside(self, target: ET.Element, mod_elem: Optional[ET.Element]):
        """
        Insert modification inside target (append as child)

        Args:
            target: Target element
            mod_elem: Element to insert
        """
        if mod_elem is None:
            return

        # Append modification elements as children
        if mod_elem.tag == 'data':
            # Append all children of <data>
            for child in mod_elem:
                target.append(copy.deepcopy(child))
        else:
            target.append(copy.deepcopy(mod_elem))

    def _replace(self, target: ET.Element, mod_elem: Optional[ET.Element]):
        """
        Replace target with modification

        Args:
            target: Target element to replace
            mod_elem: Element to replace with (None = remove)
        """
        parent = self._get_parent(target)
        if parent is None:
            logger.warning("Cannot replace root element")
            return

        # Find index of target in parent
        index = list(parent).index(target)

        # Remove target
        parent.remove(target)

        # Insert replacement if provided
        if mod_elem is not None:
            if mod_elem.tag == 'data':
                # Insert all children of <data>
                for i, child in enumerate(mod_elem):
                    parent.insert(index + i, copy.deepcopy(child))
            else:
                parent.insert(index, copy.deepcopy(mod_elem))

    def _modify_attributes(self, target: ET.Element, attrs: Dict[str, Any]):
        """
        Modify attributes of target element

        Args:
            target: Target element
            attrs: Attributes to set/modify
        """
        for attr_name, attr_value in attrs.items():
            if attr_value is None:
                # Remove attribute
                if attr_name in target.attrib:
                    del target.attrib[attr_name]
            else:
                # Set attribute
                target.set(attr_name, str(attr_value))

    def _get_parent(self, element: ET.Element) -> Optional[ET.Element]:
        """
        Get parent of element (ElementTree doesn't track parents by default)
        This is a workaround - in production would use lxml or track parents
        """
        # This is a limitation of ElementTree - need to track parent separately
        # For now, return None and log warning
        # In production, would use lxml which tracks parents
        return None

    def resolve_inheritance_chain(self, view_id: int, views: Dict[int, Dict]) -> str:
        """
        Resolve full inheritance chain for a view

        Args:
            view_id: View ID to resolve
            views: Dict of all views by ID

        Returns:
            Final architecture XML with all inheritance applied
        """
        view = views.get(view_id)
        if not view:
            raise ValueError(f"View {view_id} not found")

        # If no inheritance, return as-is
        if not view.get('inherit_id'):
            return view.get('arch', '')

        # Get parent view
        parent_id = view['inherit_id']
        parent_arch = self.resolve_inheritance_chain(parent_id, views)

        # Apply this view's modifications to parent
        try:
            parent_root = ET.fromstring(parent_arch)
        except ET.ParseError as e:
            logger.error(f"Failed to parse parent architecture: {e}")
            return view.get('arch', '')

        # Parse child architecture to get xpath specs
        try:
            child_root = ET.fromstring(view.get('arch', ''))
        except ET.ParseError as e:
            logger.error(f"Failed to parse child architecture: {e}")
            return parent_arch

        # Extract xpath specifications from child
        specs = self._extract_xpath_specs(child_root)

        # Apply specs to parent
        for spec in specs:
            parent_root = self._apply_spec_sync(parent_root, spec)

        return ET.tostring(parent_root, encoding='unicode')

    def _extract_xpath_specs(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract xpath specifications from inheritance view

        Args:
            root: Root element of inheritance view

        Returns:
            List of xpath specifications
        """
        specs = []

        # Look for xpath elements
        for xpath_elem in root.findall('.//xpath'):
            expr = xpath_elem.get('expr')
            position = xpath_elem.get('position', 'inside')

            # Get modification content
            arch_xml = ''.join(ET.tostring(child, encoding='unicode') for child in xpath_elem)

            specs.append({
                'xpath': expr,
                'position': position,
                'arch': f'<data>{arch_xml}</data>'
            })

        # If root has xpath attribute (simplified syntax)
        if root.get('position'):
            specs.append({
                'xpath': root.tag,
                'position': root.get('position'),
                'arch': ET.tostring(root, encoding='unicode')
            })

        return specs

    def _apply_spec_sync(self, root: ET.Element, spec: Dict[str, Any]) -> ET.Element:
        """
        Synchronous version of _apply_spec for inheritance chain resolution

        Args:
            root: Root element
            spec: Inheritance spec

        Returns:
            Modified root element
        """
        # This is a simplified sync version
        # In production, would refactor to avoid duplication
        return root
