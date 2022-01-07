from processor_table import *


class ProcessorExtension(ProcessorTable):

    # names for columns
    cycle = 0
    instruction_pointer = 1
    current_instruction = 2
    next_instruction = 3
    memory_pointer = 4
    memory_value = 5
    is_zero = 6

    instruction_permutation = 7
    memory_permutation = 8
    input_evaluation = 9
    output_evaluation = 10

    def __init__(self, a, b, c, d, e, f, alpha, beta, gamma, delta):
        field = a.field

        # terminal values (placeholders)
        self.instruction_permutation_terminal = field.zero()
        self.memory_permutation_terminal = field.zero()
        self.input_evaluation_terminal = field.zero()
        self.output_evaluation_terminal = field.zero()

        # names for challenges
        self.a = MPolynomial.constant(a)
        self.b = MPolynomial.constant(b)
        self.c = MPolynomial.constant(c)
        self.d = MPolynomial.constant(d)
        self.e = MPolynomial.constant(e)
        self.f = MPolynomial.constant(f)
        self.alpha = MPolynomial.constant(alpha)
        self.beta = MPolynomial.constant(beta)
        self.gamma = MPolynomial.constant(gamma)
        self.delta = MPolynomial.constant(delta)

        super(ProcessorExtension, self).__init__(field)
        self.width = 7 + 4

    @staticmethod
    def extend(processor_table, a, b, c, d, e, f, alpha, beta, gamma, delta):
        # algebra stuff
        field = processor_table.field
        xfield = a.field
        one = xfield.one()
        zero = xfield.zero()

        # prepare for loop
        instruction_permutation_running_product = one
        memory_permutation_running_product = one
        input_evaluation_running_evaluation = zero
        output_evaluation_running_evaluation = zero

        # loop over all rows
        table_extension = []
        for row in processor_table.table:
            new_row = []

            # first, copy over existing row
            new_row = [xfield.lift(nr) for nr in row]

            # next, define the additional columns

            # 1. running product for instruction permutation
            new_row += [instruction_permutation_running_product]
            instruction_permutation_running_product *= alpha - \
                a * new_row[ProcessorExtension.instruction_pointer] - \
                b * new_row[ProcessorExtension.current_instruction] - \
                c * new_row[ProcessorExtension.next_instruction]

            # 2. running product for memory access
            new_row += [memory_permutation_running_product]
            memory_permutation_running_product *= beta - d * \
                new_row[ProcessorExtension.cycle] - e * new_row[ProcessorExtension.memory_pointer] - \
                f * new_row[ProcessorExtension.memory_value]

            # 3. evaluation for input
            new_row += [input_evaluation_running_evaluation]
            if row[ProcessorExtension.current_instruction] == BaseFieldElement(ord(','), field):
                input_evaluation_running_evaluation = input_evaluation_running_evaluation * gamma \
                    + new_row[ProcessorExtension.memory_value]

            # 4. evaluation for output
            new_row += [output_evaluation_running_evaluation]
            if row[ProcessorExtension.current_instruction] == BaseFieldElement(ord('.'), field):
                output_evaluation_running_evaluation = output_evaluation_running_evaluation * delta \
                    + new_row[ProcessorExtension.memory_value]

            table_extension += [new_row]

        extended_processor_table = ProcessorExtension(
            a, b, c, d, e, f, alpha, beta, gamma, delta)
        extended_processor_table.table = table_extension

        # append terminal values
        extended_processor_table.instruction_permutation_terminal = instruction_permutation_running_product
        extended_processor_table.memory_permutation_terminal = memory_permutation_running_product
        extended_processor_table.input_evaluation_terminal = input_evaluation_running_evaluation
        extended_processor_table.output_evaluation_terminal = output_evaluation_running_evaluation

        return extended_processor_table

    def transition_constraints(self):
        # names for variables
        cycle, \
            instruction_pointer, \
            current_instruction, \
            next_instruction, \
            memory_pointer, \
            memory_value, \
            is_zero, \
            instruction_permutation, \
            memory_permutation, \
            input_evaluation, \
            output_evaluation, \
            cycle_next, \
            instruction_pointer_next, \
            current_instruction_next, \
            next_instruction_next, \
            memory_pointer_next, \
            memory_value_next, \
            is_zero_next, \
            instruction_permutation_next, \
            memory_permutation_next, \
            input_evaluation_next, \
            output_evaluation_next = MPolynomial.variables(22, self.field)

        # base AIR polynomials
        polynomials = self.transition_constraints_afo_named_variables(cycle, instruction_pointer, current_instruction, next_instruction, memory_pointer, memory_value,
                                                                      is_zero, cycle_next, instruction_pointer_next, current_instruction_next, next_instruction_next, memory_pointer_next, memory_value_next, is_zero_next)

        assert(len(polynomials) ==
               6), f"expected to have 6 transition constraint polynomials, but have {len(polynomials)}"

        # extension AIR polynomials
        # running product for instruction permutation
        polynomials += [instruction_permutation *
                        (self.alpha - self.a * instruction_pointer
                         - self.b * current_instruction
                                - self.c * next_instruction)
                        - instruction_permutation_next]
        # running product for memory permutation
        polynomials += [memory_permutation *
                        (self.beta - self.d * cycle
                         - self.e * memory_pointer - self.f * memory_value)
                        - memory_permutation_next]
        # running evaluation for input
        polynomials += [(input_evaluation_next - input_evaluation * self.gamma - memory_value) * self.ifnot_instruction(
            ',', current_instruction) + (input_evaluation_next - input_evaluation) * self.if_instruction(',', current_instruction)]
        # running evaluation for output
        polynomials += [(output_evaluation_next - output_evaluation * self.delta - memory_value) * self.ifnot_instruction(
            '.', current_instruction) + (output_evaluation_next - output_evaluation) * self.if_instruction('.', current_instruction)]

        return polynomials

    def boundary_constraints(self):
        # format: (cycle, polynomial)
        x = MPolynomial.variables(self.width, self.field)
        one = MPolynomial.constant(self.field.one())
        zero = MPolynomial.zero()
        constraints = [(0, x[self.cycle] - zero),
                       (0, x[self.instruction_pointer] - zero),
                       # (0, x[self.current_instruction] - ??),
                       # (0, x[self.next_instruction] - ??),
                       (0, x[self.memory_pointer] - zero),
                       (0, x[self.memory_value] - zero),
                       (0, x[self.is_zero] - one),
                       (0, x[self.instruction_permutation] - one),
                       (0, x[self.memory_permutation] - one),
                       (0, x[self.input_evaluation] - zero),
                       (0, x[self.output_evaluation] - zero)
                       ]
        return constraints