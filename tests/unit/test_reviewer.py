# import random

# import pytest
# from bookops_marc import Bib
# from pymarc import Field, Subfield

# from overload_web.domain import shared
# from overload_web.domain.pvf import review_service
# from overload_web.infrastructure import marc_handler


# @pytest.fixture
# def stub_full_bib(stub_bib):
#     def create_bib(library, collection, control_number, item_tag):
#         number = random.randint(0, 100)
#         barcode = f"33333{str(number).zfill(10)}"
#         if item_tag == "960":
#             field_037b = "Foo"
#             item_ind2 = " "
#         else:
#             field_037b = "OverDrive, Inc."
#             item_ind2 = "1"
#         field_list = [
#             {
#                 "tag": "037",
#                 "ind1": " ",
#                 "ind2": " ",
#                 "subfields": [
#                     {"code": "a", "value": "123"},
#                     {"code": "b", "value": field_037b},
#                 ],
#             },
#             {
#                 "tag": item_tag,
#                 "ind1": " ",
#                 "ind2": item_ind2,
#                 "subfields": [{"code": "i", "value": barcode}],
#             },
#             {
#                 "tag": "949",
#                 "ind1": " ",
#                 "ind2": " ",
#                 "subfields": [{"code": "a", "value": "*b2=a;"}],
#             },
#         ]
#         parsed_fields = []
#         bib = Bib()
#         bib.leader = "00000cam  2200517 i 4500"
#         bib.library = library
#         for field in field_list:
#             bib.add_field(
#                 Field(
#                     tag=field["tag"],
#                     indicators=(field["ind1"], field["ind2"]),
#                     subfields=[
#                         Subfield(code=i["code"], value=i["value"])
#                         for i in field["subfields"]
#                     ],
#                 )
#             )
#             parsed_fields.append(
#                 shared.ParsedField(
#                     tag=field["tag"],
#                     indicators=(field["ind1"], field["ind2"]),
#                     subfields=[
#                         shared.ParsedSubfield(code=i["code"], value=i["value"])
#                         for i in field["subfields"]
#                     ],
#                 )
#             )
#         domain_bib = stub_bib(library, collection, "cat")
#         domain_bib.binary_data = bib.as_marc()
#         domain_bib.parsed_fields = parsed_fields
#         domain_bib.barcodes = [barcode]
#         domain_bib.control_number = control_number
#         domain_bib.action = "insert"
#         return domain_bib

#     return create_bib


# @pytest.fixture(params=[("nypl", "BL"), ("nypl", "RL"), ("bpl", None)])
# def full_bib_949_item(stub_full_bib, request):
#     def create_bib(control_number):
#         return stub_full_bib(request.param[0], request.param[1], control_number, "949")

#     return create_bib


# @pytest.fixture
# def full_bib_960_item(stub_full_bib):
#     def create_bib(control_number):
#         return stub_full_bib("bpl", None, control_number, "960")

#     return create_bib


# @pytest.fixture
# def stub_reviewer():
#     return review_service.BibReviewer(handler=marc_handler.MarcUpdater())
