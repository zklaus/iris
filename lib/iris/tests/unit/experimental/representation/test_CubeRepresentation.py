# (C) British Crown Copyright 2017 - 2019, Met Office
#
# This file is part of Iris.
#
# Iris is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Iris is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Iris.  If not, see <http://www.gnu.org/licenses/>.
"""Unit tests for the `iris.cube.CubeRepresentation` class."""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# Import iris.tests first so that some things can be initialised before
# importing anything else.
import iris.tests as tests

from iris.coords import CellMethod
import iris.tests.stock as stock

from iris.experimental.representation import CubeRepresentation


@tests.skip_data
class Test__instantiation(tests.IrisTest):
    def setUp(self):
        self.cube = stock.simple_3d()
        self.representer = CubeRepresentation(self.cube)

    def test_cube_attributes(self):
        self.assertEqual(id(self.cube), self.representer.cube_id)
        self.assertStringEqual(str(self.cube), self.representer.cube_str)

    def test__heading_contents(self):
        content = set(self.representer.str_headings.values())
        self.assertEqual(len(content), 1)
        self.assertIsNone(list(content)[0])


@tests.skip_data
class Test__get_dim_names(tests.IrisTest):
    def setUp(self):
        self.cube = stock.realistic_4d()
        self.dim_names = [c.name() for c in self.cube.coords(dim_coords=True)]
        self.representer = CubeRepresentation(self.cube)

    def test_basic(self):
        result_names = self.representer._get_dim_names()
        self.assertEqual(result_names, self.dim_names)

    def test_one_anonymous_dim(self):
        self.cube.remove_coord('time')
        expected_names = ['--']
        expected_names.extend(self.dim_names[1:])
        result_names = self.representer._get_dim_names()
        self.assertEqual(result_names, expected_names)

    def test_anonymous_dims(self):
        target_dims = [1, 3]
        # Replicate this here as we're about to modify it.
        expected_names = [c.name() for c in self.cube.coords(dim_coords=True)]
        for dim in target_dims:
            this_dim_coord, = self.cube.coords(contains_dimension=dim,
                                               dim_coords=True)
            self.cube.remove_coord(this_dim_coord)
            expected_names[dim] = '--'
        result_names = self.representer._get_dim_names()
        self.assertEqual(result_names, expected_names)


@tests.skip_data
class Test__summary_content(tests.IrisTest):
    def setUp(self):
        self.cube = stock.lat_lon_cube()
        # Check we're not tripped up by names containing spaces.
        self.cube.rename('Electron density')
        self.cube.units = '1e11 e/m^3'
        self.representer = CubeRepresentation(self.cube)

    def test_name(self):
        # Check the cube name is being set and formatted correctly.
        expected = self.cube.name().replace('_', ' ').title()
        result = self.representer.name
        self.assertEqual(expected, result)

    def test_names(self):
        # Check the dimension names used as column headings are split out and
        # formatted correctly.
        expected_coord_names = [c.name().replace('_', ' ')
                                for c in self.cube.coords(dim_coords=True)]
        result_coord_names = self.representer.names[1:]
        for result in result_coord_names:
            self.assertIn(result, expected_coord_names)

    def test_units(self):
        # Check the units is being set correctly.
        expected = self.cube.units
        result = self.representer.units
        self.assertEqual(expected, result)

    def test_shapes(self):
        # Check cube dim lengths are split out correctly from the
        # summary string.
        expected = self.cube.shape
        result = self.representer.shapes
        self.assertEqual(expected, result)

    def test_ndims(self):
        expected = self.cube.ndim
        result = self.representer.ndims
        self.assertEqual(expected, result)


@tests.skip_data
class Test__get_bits(tests.IrisTest):
    def setUp(self):
        self.cube = stock.realistic_4d()
        cm = CellMethod('mean', 'time', '6hr')
        self.cube.add_cell_method(cm)
        self.representer = CubeRepresentation(self.cube)
        self.representer._get_bits(self.representer._get_lines())

    def test_population(self):
        for v in self.representer.str_headings.values():
            self.assertIsNotNone(v)

    def test_headings__dimcoords(self):
        contents = self.representer.str_headings['Dimension coordinates:']
        content_str = ','.join(content for content in contents)
        dim_coords = [c.name() for c in self.cube.dim_coords]
        for coord in dim_coords:
            self.assertIn(coord, content_str)

    def test_headings__auxcoords(self):
        contents = self.representer.str_headings['Auxiliary coordinates:']
        content_str = ','.join(content for content in contents)
        aux_coords = [c.name() for c in self.cube.aux_coords
                      if c.shape != (1,)]
        for coord in aux_coords:
            self.assertIn(coord, content_str)

    def test_headings__derivedcoords(self):
        contents = self.representer.str_headings['Auxiliary coordinates:']
        content_str = ','.join(content for content in contents)
        derived_coords = [c.name() for c in self.cube.derived_coords]
        for coord in derived_coords:
            self.assertIn(coord, content_str)

    def test_headings__scalarcoords(self):
        contents = self.representer.str_headings['Scalar coordinates:']
        content_str = ','.join(content for content in contents)
        scalar_coords = [c.name() for c in self.cube.coords()
                         if c.shape == (1,)]
        for coord in scalar_coords:
            self.assertIn(coord, content_str)

    def test_headings__attributes(self):
        contents = self.representer.str_headings['Attributes:']
        content_str = ','.join(content for content in contents)
        for attr_name, attr_value in self.cube.attributes.items():
            self.assertIn(attr_name, content_str)
            self.assertIn(attr_value, content_str)

    def test_headings__cellmethods(self):
        contents = self.representer.str_headings['Cell methods:']
        content_str = ','.join(content for content in contents)
        for cell_method in self.cube.cell_methods:
            self.assertIn(str(cell_method), content_str)


@tests.skip_data
class Test__make_header(tests.IrisTest):
    def setUp(self):
        self.cube = stock.simple_3d()
        self.representer = CubeRepresentation(self.cube)
        self.representer._get_bits(self.representer._get_lines())
        self.header_emts = self.representer._make_header().split('\n')

    def test_name_and_units(self):
        # Check the correct name and units are being written into the top-left
        # table cell.
        # This is found in the first cell after the `<th>` is defined.
        name_and_units_cell = self.header_emts[1]
        expected = '{name} ({units})'.format(name=self.cube.name(),
                                             units=self.cube.units)
        self.assertIn(expected.lower(), name_and_units_cell.lower())

    def test_number_of_columns(self):
        # There should be one headings column, plus a column per dimension.
        # Ignore opening and closing <tr> tags.
        result_cols = self.header_emts[1:-1]
        expected = self.cube.ndim + 1
        self.assertEqual(len(result_cols), expected)

    def test_row_headings(self):
        # Get only the dimension heading cells and not the headings column.
        dim_coord_names = [c.name() for c in self.cube.coords(dim_coords=True)]
        dim_col_headings = self.header_emts[2:-1]
        for coord_name, col_heading in zip(dim_coord_names, dim_col_headings):
            self.assertIn(coord_name, col_heading)


@tests.skip_data
class Test__make_shapes_row(tests.IrisTest):
    def setUp(self):
        self.cube = stock.simple_3d()
        self.representer = CubeRepresentation(self.cube)
        self.representer._get_bits(self.representer._get_lines())
        self.result = self.representer._make_shapes_row().split('\n')

    def test_row_title(self):
        title_cell = self.result[1]
        self.assertIn('Shape', title_cell)

    def test_shapes(self):
        expected_shapes = self.cube.shape
        result_shapes = self.result[2:-1]
        for expected, result in zip(expected_shapes, result_shapes):
            self.assertIn(str(expected), result)


@tests.skip_data
class Test__make_row(tests.IrisTest):
    def setUp(self):
        self.cube = stock.simple_3d()
        cm = CellMethod('mean', 'time', '6hr')
        self.cube.add_cell_method(cm)
        self.representer = CubeRepresentation(self.cube)
        self.representer._get_bits(self.representer._get_lines())

    def test__title_row(self):
        title = 'Wibble:'
        row = self.representer._make_row(title)
        # A cell for the title, an empty cell for each cube dimension, plus row
        # opening and closing tags.
        expected_len = self.cube.ndim + 3
        self.assertEqual(len(row), expected_len)
        # Check for specific content.
        row_str = '\n'.join(element for element in row)
        self.assertIn(title.strip(':'), row_str)
        expected_html_class = 'iris-title'
        self.assertIn(expected_html_class, row_str)

    def test__inclusion_row(self):
        # An inclusion row has x/- to indicate whether a coordinate describes
        # a dimension.
        title = 'time'
        body = ['x', '-', '-', '-']
        row = self.representer._make_row(title, body)
        # A cell for the title, a cell for each cube dimension, plus row
        # opening and closing tags.
        expected_len = len(body) + 3
        self.assertEqual(len(row), expected_len)
        # Check for specific content.
        row_str = '\n'.join(element for element in row)
        self.assertIn(title, row_str)
        self.assertIn('x', row_str)
        self.assertIn('-', row_str)
        expected_html_class_1 = 'iris-word-cell'
        expected_html_class_2 = 'iris-inclusion-cell'
        self.assertIn(expected_html_class_1, row_str)
        self.assertIn(expected_html_class_2, row_str)
        # We do not expect a colspan to be set.
        self.assertNotIn('colspan', row_str)

    def test__attribute_row(self):
        # An attribute row does not contain inclusion indicators.
        title = 'source'
        body = 'Iris test case'
        colspan = 5
        row = self.representer._make_row(title, body, colspan)
        # We only expect two cells here: the row title cell and one other cell
        # that spans a number of columns. We also need to open and close the
        # tr html element, giving 4 bits making up the row.
        self.assertEqual(len(row), 4)
        # Check for specific content.
        row_str = '\n'.join(element for element in row)
        self.assertIn(title, row_str)
        self.assertIn(body, row_str)
        # We expect a colspan to be set.
        colspan_str = 'colspan="{}"'.format(colspan)
        self.assertIn(colspan_str, row_str)


@tests.skip_data
class Test__expand_last_cell(tests.IrisTest):
    def setUp(self):
        self.cube = stock.simple_3d()
        self.representer = CubeRepresentation(self.cube)
        self.representer._get_bits(self.representer._get_lines())
        col_span = self.representer.ndims
        self.row = self.representer._make_row('title', body='first',
                                              col_span=col_span)

    def test_add_line(self):
        cell = self.representer._expand_last_cell(self.row[-2], 'second')
        self.assertIn('first<br>second', cell)


@tests.skip_data
class Test__make_content(tests.IrisTest):
    def setUp(self):
        self.cube = stock.simple_3d()
        self.representer = CubeRepresentation(self.cube)
        self.representer._get_bits(self.representer._get_lines())
        self.result = self.representer._make_content()

    def test_included(self):
        included = 'Dimension coordinates'
        self.assertIn(included, self.result)
        dim_coord_names = [c.name() for c in self.cube.dim_coords]
        for coord_name in dim_coord_names:
            self.assertIn(coord_name, self.result)

    def test_not_included(self):
        # `stock.simple_3d()` only contains the `Dimension coordinates` attr.
        not_included = list(self.representer.str_headings.keys())
        not_included.pop(not_included.index('Dimension coordinates:'))
        for heading in not_included:
            self.assertNotIn(heading, self.result)

    def test_handle_newline(self):
        cube = self.cube
        cube.attributes['lines'] = 'first\nsecond'
        representer = CubeRepresentation(cube)
        representer._get_bits(representer._get_lines())
        result = representer._make_content()
        self.assertIn('first<br>second', result)


@tests.skip_data
class Test_repr_html(tests.IrisTest):
    def setUp(self):
        self.cube = stock.simple_3d()
        representer = CubeRepresentation(self.cube)
        self.result = representer.repr_html()

    def test_contents_added(self):
        included = 'Dimension coordinates'
        self.assertIn(included, self.result)
        not_included = 'Auxiliary coordinates'
        self.assertNotIn(not_included, self.result)


if __name__ == '__main__':
    tests.main()
