.DEFAULT_GOAL := all
.PHONY: all run debug clean FORCE

TOP       := tb_tvsimulator
BUILD     := build
VERILATED := $(BUILD)/verilated

ifdef DEBUG
BIN       := $(BUILD)/tvsimulator_d
CXXFLAGS  := -g -O0
else
BIN       := $(BUILD)/tvsimulator
CXXFLAGS  := -O3
endif

VERILATOR_ROOT ?= $(shell verilator --getenv VERILATOR_ROOT)
VINC            := $(VERILATOR_ROOT)/include

SOURCE_FILES := src/tb_tvsimulator.sv $(shell find ../src -name "*.sv")
FLIST_FILE   := $(BUILD)/source.f

PKGS := $(filter %_pkg.sv,$(SOURCE_FILES))
SRCS := $(filter-out %_pkg.sv,$(SOURCE_FILES))
FLIST := $(PKGS) $(SRCS)

# ── Step 0: Source files .f ───────────────────────────────────────────────────
# Simple rule: packages > then source files
$(FLIST_FILE): $(SOURCE_FILES)
	@mkdir -p $(BUILD)
	@printf '%s\n' $(FLIST) > $@


# ── Step 1: Verilate ──────────────────────────────────────────────────────────
# Run verilator --cc to produce C++ model files and the generated header
# V$(TOP).h under $(VERILATED)/.
$(VERILATED)/V$(TOP).h: $(FLIST_FILE)
	@mkdir -p $(VERILATED)
	verilator --cc -j 0 --O3 \
	    -f $(FLIST_FILE) \
	    --x-assign fast --x-initial fast \
	    --top-module $(TOP) \
	    -Mdir $(VERILATED)

# ── Step 2: Compile ───────────────────────────────────────────────────────────
# Compile the generated model C++ ($(VERILATED)/*.cpp), the verilator runtime
# ($(VINC)/verilated.cpp), and the simulator entry point (src/main.cpp) into
# a single binary.  The wildcard expands at recipe time, after step 1 has run.
SDL2_INCLUDEDIR := $(shell sed -n 's/^includedir=//p' $(shell which sdl2-config))
SDL2_CFLAGS     := -I$(SDL2_INCLUDEDIR) -D_THREAD_SAFE
SDL2_LIBS       := $(shell sdl2-config --libs)

$(BIN): src/main.cpp src/DisplayManager.cpp $(VERILATED)/V$(TOP).h
	@mkdir -p $(BUILD)
	g++ -std=c++17 \
	    $(CXXFLAGS) \
	    -I$(VERILATED) \
	    -I$(VINC) \
	    -Isrc \
	    $(SDL2_CFLAGS) \
	    src/main.cpp \
	    src/DisplayManager.cpp \
	    $(VERILATED)/*.cpp \
	    $(VINC)/verilated.cpp \
	    $(VINC)/verilated_threads.cpp \
	    $(SDL2_LIBS) \
	    -o $(BIN)

all: $(BIN)

run: $(BIN)
	./$(BIN)

debug:
	$(MAKE) DEBUG=1

compile_commands.json: FORCE
	bear -- $(MAKE)

clean:
	rm -rf $(BUILD)

FORCE:
	# pass